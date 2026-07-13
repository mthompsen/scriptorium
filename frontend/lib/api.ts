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
