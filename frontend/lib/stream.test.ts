import { afterEach, expect, it, vi } from 'vitest';

import { streamMessage } from './api';

afterEach(() => {
  vi.unstubAllGlobals();
});

const SSE_BODY = [
  'event: user_message\ndata: {"id":"m1","role":"user","content":"PTO?","citations":[]}\n\n',
  'event: tool\ndata: {"name":"search_documents","summary":"3 result(s)"}\n\n',
  'event: token\ndata: {"text":"25 days "}\n\n',
  'event: token\ndata: {"text":"[ab12cd34-0]."}\n\n',
  'event: final\ndata: {"message":{"id":"m2","role":"assistant","content":"25 days [ab12cd34-0].","citations":[{"chunk_id":"ab12cd34-0","document_id":"d","snippet":"…"}]},"grounded":true}\n\n',
].join('');

it('parses SSE events from a chunked stream, including split chunks', async () => {
  // Split at awkward byte positions to prove incremental parsing works.
  const chunks = [SSE_BODY.slice(0, 41), SSE_BODY.slice(41, 150), SSE_BODY.slice(150)];
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(new TextEncoder().encode(chunk));
      }
      controller.close();
    },
  });
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response(stream, { status: 200 })),
  );

  const tokens: string[] = [];
  const tools: string[] = [];
  let finalContent = '';
  let userContent = '';

  await streamMessage('session-1', 'PTO?', {
    onUserMessage: (m) => (userContent = m.content),
    onToken: (t) => tokens.push(t),
    onTool: (t) => tools.push(t.name),
    onFinal: ({ message }) => (finalContent = message.content),
  });

  expect(userContent).toBe('PTO?');
  expect(tools).toEqual(['search_documents']);
  expect(tokens.join('')).toBe('25 days [ab12cd34-0].');
  expect(finalContent).toBe('25 days [ab12cd34-0].');
});
