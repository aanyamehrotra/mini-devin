# Mini-Devin

Mini-Devin is an autonomous AI coding agent that takes a programming request in natural language, plans the solution, generates code, executes it, reviews execution results, and automatically rewrites the code when errors occur.

The project is inspired by autonomous software engineering systems such as Devin and OpenHands, but is being built from scratch to understand the architecture and engineering behind these systems.

## Features

Current capabilities include:

* Natural language task planning
* AI-based code generation
* Multi-file project generation
* Automatic code execution
* Execution in isolated workspaces
* Capture of stdout, stderr, and exit codes
* AI-powered code review
* Automatic code rewriting
* Retry loop for failed executions
* FastAPI REST API

## Architecture

```
User Prompt
      │
      ▼
Planner Agent
      │
      ▼
Coder Agent
      │
      ▼
Generated Project
      │
      ▼
Execution Engine
      │
      ▼
Execution Result
      │
      ▼
Reviewer Agent
      │
      ▼
Rewrite Agent
      │
      ▼
Retry (until success or max retries)
```

## Tech Stack

* Python
* FastAPI
* Gemini API
* Pydantic
* Subprocess
* UUID-based workspace isolation

## Project Structure

```
MINI-DEVIN/
│
├── app/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── coder.py
│   │   ├── reviewer.py
│   │   └── manager.py
│   │
│   ├── executor/
│   │   └── runner.py
│   │
│   ├── routes/
│   │   └── chat.py
│   │
│   ├── services/
│   │   └── llm/
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   └── main.py
│
├── workspace/
├── requirements.txt
└── README.md
```

## Current Workflow

1. The user submits a programming task.
2. The Planner Agent creates a structured implementation plan.
3. The Coder Agent generates the project files.
4. The Execution Engine creates an isolated workspace and runs the generated project.
5. Execution output and errors are collected.
6. The Reviewer Agent analyzes the execution results.
7. The Rewrite Agent improves the implementation when necessary.
8. The system retries until the project succeeds or reaches the maximum retry limit.

## Current Status

Implemented:

* FastAPI backend
* Planner Agent
* Coder Agent
* Reviewer Agent
* Rewrite Agent
* Manager orchestration
* Multi-file code generation
* Workspace isolation
* Execution engine
* Automatic retry mechanism
* Timeout handling
* Structured execution reports

In Progress:

* Improved handling of interactive programs
* Better execution feedback for autonomous debugging

## Roadmap

Short term

* Virtual environment creation per workspace
* Automatic dependency installation
* Better runtime error classification
* Docker-based sandbox execution

Medium term

* Retrieval-Augmented Generation (RAG)
* LangGraph-based orchestration
* Streaming execution updates
* React frontend

Long term

* GitHub integration
* Pull request generation
* Repository-aware coding
* Automated test generation
* Cloud deployment

## Motivation

The goal of this project is to understand how modern autonomous coding agents work internally rather than simply using existing frameworks.

Each component is implemented separately to explore planning, code generation, execution, debugging, and iterative improvement as independent agents working together in a feedback loop.


