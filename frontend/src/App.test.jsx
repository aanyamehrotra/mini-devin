import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';
import { runTask } from './stream.js';
vi.mock('./stream.js',()=>({runTask:vi.fn()}));

const code = { files: [{path:'main.py',content:'print("hello")'}, {path:'helper.py',content:'answer = 42'}] };
const execution = {stdout:'hello output',stderr:'',exit_code:0,execution_time:.1};
const review = {feedback:'Matches the request'};
const result = {plan:{goal:'Print hello'},code,execution,review,attempts:[
  {attempt:1,success:false,code,execution:{...execution,stdout:'first attempt',stderr:'NameError'},review:{feedback:'Fix the name'}},
  {attempt:2,success:true,code,execution,review}
]};
beforeEach(()=>vi.resetAllMocks());

async function start() {
  const user=userEvent.setup();
  render(<App/>);
  await user.type(screen.getByLabelText('Your task'),'Print hello');
  await user.click(screen.getByRole('button',{name:/Build project/}));
  return user;
}

describe('workspace',()=>{
  it('disables an empty submission and fills example prompts',async()=>{
    const user=userEvent.setup();render(<App/>);
    expect(screen.getByRole('button',{name:/Build project/}).disabled).toBe(true);
    await user.click(screen.getByRole('button',{name:/Fibonacci/}));
    expect(screen.getByLabelText('Your task').value).toContain('Fibonacci');
  });
  it('renders results, switches files and inspects failed attempts',async()=>{
    runTask.mockImplementation(async(prompt,onEvent)=>{
      onEvent({type:'stage',data:{stage:'plan',status:'completed'}});
      onEvent({type:'complete',data:{success:true,result}});
    });
    const user=await start();
    expect(await screen.findByText('hello output')).toBeTruthy();
    expect(screen.getByText('print("hello")')).toBeTruthy();
    await user.click(screen.getByRole('button',{name:'helper.py'}));
    expect(screen.getByText('answer = 42')).toBeTruthy();
    await user.selectOptions(screen.getByLabelText('Attempt'),'0');
    expect(screen.getByText('first attempt')).toBeTruthy();
    expect(screen.getByText('NameError')).toBeTruthy();
    expect(screen.getByText('Fix the name')).toBeTruthy();
  });
  it('displays a provider error and allows retry',async()=>{
    runTask.mockImplementation(async(prompt,onEvent)=>onEvent({type:'error',data:{stage:'planner',error:'provider_failure'}}));
    await start();
    expect((await screen.findByRole('alert')).textContent).toContain('model provider');
    expect(screen.getByRole('button',{name:/Build project/}).disabled).toBe(false);
  });
  it('stops updates using AbortController without claiming work was killed',async()=>{
    runTask.mockImplementation((prompt,onEvent,signal)=>new Promise((resolve,reject)=>{
      signal.addEventListener('abort',()=>reject(new DOMException('Stopped','AbortError')));
    }));
    const user=await start();
    await user.click(screen.getByRole('button',{name:'Stop updates'}));
    expect((await screen.findByRole('alert')).textContent).toContain('Work already running may finish');
    await waitFor(()=>expect(screen.getByRole('button',{name:/Build project/}).disabled).toBe(false));
  });
  it('shows transport errors without losing the prompt',async()=>{
    runTask.mockRejectedValue(new Error('The connection ended before a final result.'));
    await start();
    expect((await screen.findByRole('alert')).textContent).toContain('connection ended');
    expect(screen.getByLabelText('Your task').value).toBe('Print hello');
  });
});

it('keeps references off by default and submits explicit opt-in',async()=>{
  runTask.mockImplementation(async(prompt,onEvent)=>onEvent({type:'error',data:{error:'provider_failure'}}));
  const user=userEvent.setup();render(<App/>);
  const checkbox=screen.getByRole('checkbox',{name:/Use project references/});
  expect(checkbox.checked).toBe(false);
  await user.click(checkbox);
  await user.type(screen.getByLabelText('Your task'),'hello');
  await user.click(screen.getByRole('button',{name:/Build project/}));
  expect(runTask.mock.calls[0][3]).toBe(true);
});

it('shows supplied citations and excerpts without claiming proven grounding',async()=>{
  const context={status:'ready',sources:[{citation:'guide.md:1-2',text:'A useful example',truncated:false}]};
  runTask.mockImplementation(async(prompt,onEvent)=>onEvent({type:'complete',data:{success:true,result:{...result,context}}}));
  await start();
  expect(await screen.findByText('guide.md:1-2')).toBeTruthy();
  expect(screen.getByText('A useful example')).toBeTruthy();
  expect(screen.getByText(/do not prove the result is correct/)).toBeTruthy();
});

it('passes an optional workspace token from memory',async()=>{
  runTask.mockImplementation(async(prompt,onEvent)=>onEvent({type:'error',data:{error:'provider_failure'}}));
  const user=userEvent.setup();render(<App/>);
  await user.click(screen.getByText('Workspace access'));
  await user.type(screen.getByLabelText('Workspace access token (if configured)'),'workspace-fixture');
  await user.type(screen.getByLabelText('Your task'),'hello');
  await user.click(screen.getByRole('button',{name:/Build project/}));
  expect(runTask.mock.calls[0][4]).toBe('workspace-fixture');
  expect(screen.getByLabelText('Workspace access token (if configured)').type).toBe('password');
});
