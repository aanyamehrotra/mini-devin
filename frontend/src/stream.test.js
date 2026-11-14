// @vitest-environment node
import { describe, it, expect, vi } from 'vitest';
import { readEvents, runTask } from './stream.js';

const result = { attempts: [{ success: true }] };
const frame = (type, data, newline='\n') => `event: ${type}${newline}data: ${JSON.stringify(data)}${newline}${newline}`;
function body(chunks) {
  return new ReadableStream({ start(controller) { for (const chunk of chunks) controller.enqueue(chunk); controller.close(); } });
}
const bytes = text => new TextEncoder().encode(text);

describe('SSE reader', () => {
  it('handles one-byte chunks, split Unicode, CRLF, and multiple events', async () => {
    const text = frame('stage', {stage:'plan',text:'café 🐍'}, '\r\n') + frame('complete',{success:true,result},'\r\n');
    const events=[];
    await readEvents(body([...bytes(text)].map(n=>Uint8Array.of(n))), e=>events.push(e));
    expect(events).toHaveLength(2);
    expect(events[0].data.text).toBe('café 🐍');
    expect(events[1].type).toBe('complete');
  });
  it('joins multiline data and ignores comments/IDs', async () => {
    const text = ': keepalive\nid: 1\nevent: error\ndata: {"error":\ndata: "provider_failure"}\n\n';
    const events=[];
    await readEvents(body([bytes(text)]), e=>events.push(e));
    expect(events[0]).toEqual({type:'error',data:{error:'provider_failure'}});
  });
  it('reports premature EOF', async () => {
    await expect(readEvents(body([bytes(frame('stage',{stage:'plan'}))]), ()=>{})).rejects.toThrow('before a final result');
  });
  it('rejects malformed event data', async () => {
    await expect(readEvents(body([bytes('event: error\ndata: nope\n\n')]), ()=>{})).rejects.toThrow('invalid progress');
  });
  it('rejects incomplete result instead of crashing the UI', async () => {
    await expect(readEvents(body([bytes(frame('complete',{result:{}}))]), ()=>{})).rejects.toThrow('incomplete project');
  });
  it('honors abort before reading', async () => {
    const controller = new AbortController(); controller.abort();
    await expect(readEvents(body([]), ()=>{}, controller.signal)).rejects.toHaveProperty('name','AbortError');
  });
});

describe('HTTP contract', () => {
  it('posts prompt to the same-origin proxy and consumes SSE', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(body([bytes(frame('cancelled',{reason:'client_disconnected'}))]),{headers:{'content-type':'text/event-stream'}}));
    const receive=vi.fn();
    try {
      await runTask('hello', receive);
      expect(fetchMock).toHaveBeenCalledWith('/api/chat/stream',expect.objectContaining({method:'POST',body:'{"prompt":"hello"}'}));
      expect(receive).toHaveBeenCalledWith({type:'cancelled',data:{reason:'client_disconnected'}});
    } finally {fetchMock.mockRestore();}
  });
  it.each([[502,'text/event-stream','request failed'],[200,'text/html','unexpected response']])('handles status %i and %s',async(status,type,message)=>{
    const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('error',{status,headers:{'content-type':type}}));
    try {await expect(runTask('hello',()=>{})).rejects.toThrow(message);} finally {fetchMock.mockRestore();}
  });
});

it('includes context opt-in only when requested', async () => {
  const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(body([bytes(frame('cancelled',{reason:'client_disconnected'}))]),{headers:{'content-type':'text/event-stream'}}));
  try {
    await runTask('hello',()=>{},undefined,true);
    expect(fetchMock).toHaveBeenCalledWith('/api/chat/stream',expect.objectContaining({body:'{"prompt":"hello","use_context":true}'}));
  } finally {fetchMock.mockRestore();}
});

it('sends the workspace token only as an authorization header', async () => {
  const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(body([bytes(frame('cancelled',{reason:'client_disconnected'}))]),{headers:{'content-type':'text/event-stream'}}));
  try {
    await runTask('hello',()=>{},undefined,false,'workspace-fixture');
    const options=fetchMock.mock.calls[0][1];
    expect(options.headers.Authorization).toBe('Bearer workspace-fixture');
    expect(options.body).not.toContain('workspace-fixture');
  } finally {fetchMock.mockRestore();}
});

it('explains access-token failures',async()=>{
  const fetchMock=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response('',{status:401}));
  try {await expect(runTask('hello',()=>{})).rejects.toThrow('workspace access token');} finally {fetchMock.mockRestore();}
});
