'use client';

import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useRef, useState } from 'react';

import {
  api,
  ApiError,
  ChatMessage,
  ChatSession,
  postJson,
  streamMessage,
  ToolEvent,
} from '@/lib/api';

interface DisplayMessage extends ChatMessage {
  tools?: ToolEvent[];
  live?: boolean;
}

export default function ChatPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api('/auth/me').catch((e: unknown) => {
      if (e instanceof ApiError && e.status === 401) {
        router.replace('/login');
      }
    });
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const patchLive = (patch: (live: DisplayMessage) => DisplayMessage) => {
    setMessages((prev) =>
      prev.map((message) => (message.live ? patch(message) : message)),
    );
  };

  async function send(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    setInput('');
    try {
      let id = sessionId;
      if (!id) {
        const session = await postJson<ChatSession>('/chat/sessions', {
          title: content.slice(0, 60),
        });
        id = session.id;
        setSessionId(id);
      }
      // Live placeholder that tokens and tool events stream into.
      setMessages((prev) => [
        ...prev,
        { id: 'live', role: 'assistant', content: '', citations: [], tools: [], live: true },
      ]);
      await streamMessage(id, content, {
        onUserMessage: (message) =>
          setMessages((prev) => [
            ...prev.filter((m) => !m.live),
            message,
            { id: 'live', role: 'assistant', content: '', citations: [], tools: [], live: true },
          ]),
        onTool: (tool) =>
          patchLive((live) => ({ ...live, tools: [...(live.tools ?? []), tool] })),
        onToken: (text) => patchLive((live) => ({ ...live, content: live.content + text })),
        onFinal: ({ message }) =>
          setMessages((prev) =>
            prev.map((m) => (m.live ? { ...message, tools: m.tools } : m)),
          ),
        onError: (message) => {
          setError(message);
          setMessages((prev) => prev.filter((m) => !m.live));
        },
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        router.replace('/login');
        return;
      }
      setError(e instanceof ApiError ? e.message : 'Failed to send message');
      setMessages((prev) => prev.filter((m) => !m.live));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="flex h-[70vh] flex-col space-y-4">
      <h1 className="text-2xl font-semibold">Chat</h1>
      <div
        aria-live="polite"
        className="flex-1 space-y-3 overflow-y-auto rounded-md border border-slate-200 bg-white p-4"
      >
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">
            Ask a question about your documents — the agent searches the corpus, shows its tool
            calls, and cites its sources. Local inference can take a minute.
          </p>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={
              message.role === 'user'
                ? 'ml-auto max-w-[80%] rounded-lg bg-slate-900 px-3 py-2 text-sm text-white'
                : 'mr-auto max-w-[80%] rounded-lg bg-slate-100 px-3 py-2 text-sm'
            }
          >
            {(message.tools?.length ?? 0) > 0 && (
              <details className="mb-2 border-b border-slate-300 pb-1 text-xs text-slate-600">
                <summary className="cursor-pointer font-medium">
                  Agent activity ({message.tools!.length} tool call
                  {message.tools!.length > 1 ? 's' : ''})
                </summary>
                <ul className="mt-1 space-y-1">
                  {message.tools!.map((tool, index) => (
                    <li key={index}>
                      <code className="rounded bg-slate-200 px-1">{tool.name}</code>{' '}
                      {tool.summary}
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <p>
              {message.content}
              {message.live && <span className="animate-pulse">▋</span>}
            </p>
            {message.citations?.length > 0 && (
              <details className="mt-2 border-t border-slate-300 pt-1 text-xs text-slate-600">
                <summary className="cursor-pointer font-medium">
                  {message.citations.length} source
                  {message.citations.length > 1 ? 's' : ''}
                </summary>
                <ul className="mt-1 space-y-1">
                  {message.citations.map((citation) => (
                    <li key={citation.chunk_id}>
                      <code className="rounded bg-slate-200 px-1">[{citation.chunk_id}]</code>{' '}
                      {citation.snippet}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {error && (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      )}
      <form onSubmit={send} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something…"
          aria-label="Message"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </section>
  );
}
