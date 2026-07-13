import { Inject, Injectable } from '@nestjs/common';
import { Pool } from 'pg';

import { PG_POOL } from '../pg/pg.module';

export interface ChatSessionRow {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  created_at: string;
}

export interface ChatCitation {
  chunk_id: string;
  document_id: string;
  snippet: string;
}

export interface ChatMessageRow {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  citations: ChatCitation[];
  created_at: string;
}

@Injectable()
export class ChatRepository {
  constructor(@Inject(PG_POOL) private readonly pool: Pool) {}

  async createSession(tenantId: string, userId: string, title: string): Promise<ChatSessionRow> {
    const result = await this.pool.query(
      `INSERT INTO chat_sessions (tenant_id, user_id, title)
       VALUES ($1, $2, $3) RETURNING *`,
      [tenantId, userId, title],
    );
    return result.rows[0] as ChatSessionRow;
  }

  async listSessions(tenantId: string, userId: string): Promise<ChatSessionRow[]> {
    const result = await this.pool.query(
      `SELECT * FROM chat_sessions
        WHERE tenant_id = $1 AND user_id = $2
        ORDER BY created_at DESC`,
      [tenantId, userId],
    );
    return result.rows as ChatSessionRow[];
  }

  async findSession(
    tenantId: string,
    userId: string,
    sessionId: string,
  ): Promise<ChatSessionRow | undefined> {
    const result = await this.pool.query(
      `SELECT * FROM chat_sessions WHERE tenant_id = $1 AND user_id = $2 AND id = $3`,
      [tenantId, userId, sessionId],
    );
    return result.rows[0] as ChatSessionRow | undefined;
  }

  async insertMessage(
    sessionId: string,
    role: ChatMessageRow['role'],
    content: string,
    citations: ChatCitation[] = [],
  ): Promise<ChatMessageRow> {
    const result = await this.pool.query(
      `INSERT INTO chat_messages (session_id, role, content, citations)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [sessionId, role, content, JSON.stringify(citations)],
    );
    return result.rows[0] as ChatMessageRow;
  }

  async listMessages(sessionId: string): Promise<ChatMessageRow[]> {
    const result = await this.pool.query(
      `SELECT * FROM chat_messages WHERE session_id = $1 ORDER BY created_at, id`,
      [sessionId],
    );
    return result.rows as ChatMessageRow[];
  }

  /** Backfill the trace → message link once the assistant row exists (ADR-0005). */
  async linkRunToMessage(runId: string, messageId: string): Promise<void> {
    await this.pool.query(`UPDATE agent_runs SET message_id = $2 WHERE id = $1`, [
      runId,
      messageId,
    ]);
  }
}
