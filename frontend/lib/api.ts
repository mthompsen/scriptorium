/** Typed client for the BFF. The JWT travels in an HttpOnly cookie (ADR-0003). */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:3001';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}/api/v1${path}`, {
    credentials: 'include',
    ...init,
  });
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = (await response.json()) as { message?: string | string[] };
      if (body.message) {
        message = Array.isArray(body.message) ? body.message.join('; ') : body.message;
      }
    } catch {
      // non-JSON error body — keep the status text
    }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

export const postJson = <T>(path: string, body: unknown): Promise<T> =>
  api<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

export interface Principal {
  userId: string;
  tenantId: string;
  email: string;
  roles: string[];
}

export interface DocumentRow {
  id: string;
  title: string;
  mime_type: string;
  status: string;
  created_at: string;
}

export interface ChatCitation {
  chunk_id: string;
  document_id: string;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  citations: ChatCitation[];
}

export interface ChatSession {
  id: string;
  title: string;
}

export interface ToolEvent {
  name: string;
  summary: string;
}

export interface StreamHandlers {
  onUserMessage?: (message: ChatMessage) => void;
  onToken?: (text: string) => void;
  onTool?: (tool: ToolEvent) => void;
  onFinal?: (data: { message: ChatMessage; grounded: boolean }) => void;
  onError?: (message: string) => void;
}

/**
 * Sends a chat message and consumes the SSE reply over POST (ADR-0005).
 * EventSource cannot POST, so the stream is parsed from fetch's body.
 */
export async function streamMessage(
  sessionId: string,
  content: string,
  handlers: StreamHandlers,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!response.ok || !response.body) {
    throw new ApiError(response.status, response.statusText);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    let boundary: number;
    while ((boundary = buffer.indexOf('\n\n')) >= 0) {
      dispatchSseBlock(buffer.slice(0, boundary), handlers);
      buffer = buffer.slice(boundary + 2);
    }
  }
}

function dispatchSseBlock(block: string, handlers: StreamHandlers): void {
  let event = '';
  let data = '';
  for (const line of block.split('\n')) {
    if (line.startsWith('event: ')) {
      event = line.slice(7).trim();
    } else if (line.startsWith('data: ')) {
      data = line.slice(6);
    }
  }
  if (!event || !data) {
    return;
  }
  const payload = JSON.parse(data) as Record<string, unknown>;
  switch (event) {
    case 'user_message':
      handlers.onUserMessage?.(payload as unknown as ChatMessage);
      break;
    case 'token':
      handlers.onToken?.(payload.text as string);
      break;
    case 'tool':
      handlers.onTool?.(payload as unknown as ToolEvent);
      break;
    case 'final':
      handlers.onFinal?.(payload as unknown as { message: ChatMessage; grounded: boolean });
      break;
    case 'error':
      handlers.onError?.((payload.message as string) ?? 'stream failed');
      break;
  }
}
