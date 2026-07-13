import { Injectable, NotFoundException } from '@nestjs/common';

import { TenantContext } from '../auth/tenant-context';
import { ChatMessageRow, ChatRepository, ChatSessionRow } from './chat.repository';

/** M1 stub reply — replaced by the RAG answer path in M2 (DESIGN.md Section 15). */
const echoReply = (content: string): string =>
  `Echo (stub — grounded answers arrive in M2): ${content}`;

@Injectable()
export class ChatService {
  constructor(
    private readonly tenant: TenantContext,
    private readonly repository: ChatRepository,
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
    const assistant = await this.repository.insertMessage(
      sessionId,
      'assistant',
      echoReply(content),
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
