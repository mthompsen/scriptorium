'use client';

import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useRef, useState } from 'react';

import { api, ApiError, ChatMessage, ChatSession, postJson } from '@/lib/api';

export default function ChatPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
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

  async function send(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let id = sessionId;
      if (!id) {
        const session = await postJson<ChatSession>('/chat/sessions', {
          title: content.slice(0, 60),
        });
        id = session.id;
        setSessionId(id);
      }
      const result = await postJson<{ user: ChatMessage; assistant: ChatMessage }>(
        `/chat/sessions/${id}/messages`,
        { content },
      );
      setMessages((prev) => [...prev, result.user, result.assistant]);
      setInput('');
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        router.replace('/login');
        return;
      }
      setError(e instanceof ApiError ? e.message : 'Failed to send message');
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
            Ask a question about your documents — answers are grounded in the corpus and cited.
            Local model inference can take up to a minute.
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
            <p>{message.content}</p>
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
