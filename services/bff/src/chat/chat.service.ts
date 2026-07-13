import { Injectable, NotFoundException } from '@nestjs/common';

import { TenantContext } from '../auth/tenant-context';
import { AgentClient } from './agent.client';
import { ChatMessageRow, ChatRepository, ChatSessionRow } from './chat.repository';

@Injectable()
export class ChatService {
  constructor(
    private readonly tenant: TenantContext,
    private readonly repository: ChatRepository,
    private readonly agent: AgentClient,
  ) {}

  createSession(title?: string): Promise<ChatSessionRow> {
    return this.repository.createSession(
      this.tenant.tenantId,
      this.tenant.userId,
      title?.trim() || 'New session',
    );
  }

  listSessions(): Promise<ChatSessionRow[]> {
    return this.repository.listSessions(this.tenant.tenantId, this.tenant.userId);
  }

  async sendMessage(
    sessionId: string,
    content: string,
  ): Promise<{ user: ChatMessageRow; assistant: ChatMessageRow }> {
    await this.requireSession(sessionId);
    const user = await this.repository.insertMessage(sessionId, 'user', content);
    // Grounded RAG answer from the reason path (M2, ADR-0004); the tenant
    // scope is injected server-side — never taken from the client.
    const answer = await this.agent.answer(this.tenant.tenantId, content);
    const assistant = await this.repository.insertMessage(
      sessionId,
      'assistant',
      answer.answer,
      answer.citations,
    );
    return { user, assistant };
  }

  async listMessages(sessionId: string): Promise<ChatMessageRow[]> {
    await this.requireSession(sessionId);
    return this.repository.listMessages(sessionId);
  }

  private async requireSession(sessionId: string): Promise<void> {
    const session = await this.repository.findSession(
      this.tenant.tenantId,
      this.tenant.userId,
      sessionId,
    );
    if (!session) {
      throw new NotFoundException('Chat session not found');
    }
  }
}
