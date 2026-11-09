"""LangGraph orchestration for bounded, review-driven project generation."""

from typing import TypedDict

from app.agents.planner import plan_task
from app.agents.coder import write_code, rewrite_code
from app.agents.reviewer import review_code
from app.executor.runner import execute_code
from app.models.schemas import Plan, CodeResponse, ExecutionResult, ReviewResult

MAX_RETRIES = 3  # Total execution attempts, including the first generation.


class AgentState(TypedDict, total=False):
    user_prompt: str
    plan: Plan
    code: CodeResponse
    execution: ExecutionResult
    review: ReviewResult
    attempts: list[dict]


def build_graph(max_attempts: int = MAX_RETRIES):
    from langchain_core.runnables import RunnableLambda
    from langgraph.graph import END, START, StateGraph

    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError('max_attempts must be a positive integer')

    def plan(state):
        return {'plan': plan_task(state['user_prompt'])}

    def generate(state):
        if state['attempts']:
            code = rewrite_code(state['plan'], state['code'], state['review'].feedback)
        else:
            code = write_code(state['plan'], state['user_prompt'])
        return {'code': code}

    def execute(state):
        return {'execution': execute_code(state['code'])}

    def review(state):
        execution = state['execution']
        if execution.error_type == 'ExecutionEnvironment':
            # An unavailable engine cannot be repaired by generating different code.
            result = ReviewResult(success=False, feedback=execution.stderr,
                                  failure_source='execution_environment')
        else:
            result = review_code(state['plan'], state['code'], execution, state['user_prompt'])
            if result.success and not execution.success:
                result = ReviewResult(success=False,
                                      feedback='Execution failed despite review approval. ' + execution.stderr,
                                      failure_source='code')
        attempt = {
            'attempt': len(state['attempts']) + 1,
            'code': state['code'], 'execution': execution, 'review': result,
            'success': execution.success and result.success,
        }
        return {'review': result, 'attempts': [*state['attempts'], attempt]}

    def route(state):
        if (state['attempts'][-1]['success']
                or state['review'].failure_source == 'execution_environment'
                or len(state['attempts']) >= max_attempts):
            return END
        return 'generate'

    graph = StateGraph(AgentState)
    for name, function in [('plan', plan), ('generate', generate),
                           ('execute', execute), ('review', review)]:
        graph.add_node(name, RunnableLambda(function))
    graph.add_edge(START, 'plan')
    graph.add_edge('plan', 'generate')
    graph.add_edge('generate', 'execute')
    graph.add_edge('execute', 'review')
    graph.add_conditional_edges('review', route, {'generate': 'generate', END: END})
    return graph.compile()


def run_agent(user_prompt: str):
    state = build_graph(MAX_RETRIES).invoke(
        {'user_prompt': user_prompt, 'attempts': []},
        config={'recursion_limit': 3 * MAX_RETRIES + 3},
    )
    return {key: state[key] for key in ('plan', 'code', 'execution', 'review', 'attempts')}


async def stream_agent(user_prompt: str, *, cancelled=None):
    """Stream completed stages and a terminal result; cancel between stages.

    Synchronous provider/executor calls already running cannot be forcibly stopped.
    """
    state = {'user_prompt': user_prompt, 'attempts': []}
    updates = build_graph(MAX_RETRIES).astream(
        state, stream_mode='updates',
        config={'recursion_limit': 3 * MAX_RETRIES + 3},
    )
    try:
        while True:
            if cancelled is not None and await cancelled():
                yield {'event': 'cancelled', 'data': {'reason': 'client_disconnected'}}
                return
            try:
                update = await anext(updates)
            except StopAsyncIteration:
                break
            for stage, changes in update.items():
                state.update(changes)
                data = {'stage': stage, 'status': 'completed'}
                if stage != 'plan':
                    data['attempt'] = len(state['attempts']) + (stage != 'review')
                yield {'event': 'stage', 'data': data}
        result = {key: state[key] for key in ('plan', 'code', 'execution', 'review', 'attempts')}
        yield {'event': 'complete', 'data': {
            'success': state['attempts'][-1]['success'], 'result': result,
        }}
    finally:
        await updates.aclose()
