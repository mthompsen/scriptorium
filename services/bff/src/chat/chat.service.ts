import { BadGatewayException, Injectable, NotFoundException } from '@nestjs/common';

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

  /**
   * Streams the agent's answer (M3, ADR-0005): the user message is stored up
   * front, agent events are re-emitted to the caller, and the assistant
   * message is persisted (and linked to the trace) when the final event
   * arrives. The tenant scope is injected server-side — never client-supplied.
   */
  async *sendMessageStream(
    sessionId: string,
    content: string,
  ): AsyncGenerator<{ event: string; data: Record<string, unknown> }> {
    await this.requireSession(sessionId);
    const user = await this.repository.insertMessage(sessionId, 'user', content);
    yield { event: 'user_message', data: user as unknown as Record<string, unknown> };

    let runId: string | undefined;
    for await (const agentEvent of this.agent.answerStream(this.tenant.tenantId, content)) {
      if (agentEvent.event === 'run_start') {
        runId = agentEvent.data.run_id as string;
        yield agentEvent;
      } else if (agentEvent.event === 'final') {
        const final = agentEvent.data as unknown as {
          answer: string;
          citations: ChatMessageRow['citations'];
          run_id: string;
        };
        const assistant = await this.repository.insertMessage(
          sessionId,
          'assistant',
          final.answer,
          final.citations ?? [],
        );
        if (runId) {
          await this.repository.linkRunToMessage(runId, assistant.id);
        }
        yield {
          event: 'final',
          data: { ...agentEvent.data, message: assistant } as Record<string, unknown>,
        };
      } else {
        yield agentEvent;
      }
    }
  }

  /** Non-streaming variant for scripts and tests: awaits the final event. */
  async sendMessage(
    sessionId: string,
    content: string,
  ): Promise<{ user: ChatMessageRow; assistant: ChatMessageRow }> {
    let user: ChatMessageRow | undefined;
    let assistant: ChatMessageRow | undefined;
    for await (const event of this.sendMessageStream(sessionId, content)) {
      if (event.event === 'user_message') {
        user = event.data as unknown as ChatMessageRow;
      } else if (event.event === 'final') {
        assistant = (event.data as { message?: ChatMessageRow }).message;
      }
    }
    if (!user || !assistant) {
      throw new BadGatewayException('Agent stream ended without a final answer');
    }
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
