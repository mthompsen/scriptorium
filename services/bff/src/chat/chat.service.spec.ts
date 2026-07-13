import { BadGatewayException, NotFoundException } from '@nestjs/common';

import type { TenantContext } from '../auth/tenant-context';
import type { AgentClient, AgentStreamEvent } from './agent.client';
import type { ChatRepository } from './chat.repository';
import { ChatService } from './chat.service';

const tenant = { tenantId: 'tenant-1', userId: 'user-1' } as TenantContext;
const session = { id: 'session-1', tenant_id: 'tenant-1', user_id: 'user-1' };

const citation = { chunk_id: 'ab12cd34-0', document_id: 'doc-1', snippet: 'PTO is 25 days.' };

const agentEvents = (): AgentStreamEvent[] => [
  { event: 'run_start', data: { run_id: 'run-1' } },
  { event: 'tool', data: { name: 'search_documents', summary: '1 result(s)' } },
  { event: 'token', data: { text: 'You get 25 days ' } },
  { event: 'token', data: { text: '[ab12cd34-0].' } },
  {
    event: 'final',
    data: {
      run_id: 'run-1',
      answer: 'You get 25 days [ab12cd34-0].',
      citations: [citation],
      grounded: true,
    },
  },
];

const build = (events: AgentStreamEvent[] = agentEvents()) => {
  let messageCounter = 0;
  const repository = {
    createSession: jest.fn().mockResolvedValue(session),
    listSessions: jest.fn().mockResolvedValue([session]),
    findSession: jest.fn().mockResolvedValue(session),
    insertMessage: jest
      .fn()
      .mockImplementation(
        (sessionId: string, role: string, content: string, citations: unknown[] = []) =>
          Promise.resolve({
            id: `msg-${++messageCounter}`,
            session_id: sessionId,
            role,
            content,
            citations,
          }),
      ),
    listMessages: jest.fn().mockResolvedValue([]),
    linkRunToMessage: jest.fn().mockResolvedValue(undefined),
  };
  const agent = {
    // eslint-disable-next-line @typescript-eslint/require-await
    answerStream: jest.fn().mockImplementation(async function* () {
      yield* events;
    }),
  };
  return {
    repository,
    agent,
    service: new ChatService(
      tenant,
      repository as unknown as ChatRepository,
      agent as unknown as AgentClient,
    ),
  };
};

const collect = async (iterable: AsyncGenerator<{ event: string; data: unknown }>) => {
  const out: { event: string; data: unknown }[] = [];
  for await (const item of iterable) {
    out.push(item);
  }
  return out;
};

describe('ChatService (streaming)', () => {
  it('stores the user message, re-emits agent events, and persists the final answer', async () => {
    const { service, repository, agent } = build();

    const events = await collect(service.sendMessageStream('session-1', 'How much PTO?'));

    expect(agent.answerStream).toHaveBeenCalledWith('tenant-1', 'How much PTO?');
    expect(events.map((e) => e.event)).toEqual([
      'user_message',
      'run_start',
      'tool',
      'token',
      'token',
      'final',
    ]);
    expect(repository.insertMessage).toHaveBeenNthCalledWith(
      1,
      'session-1',
      'user',
      'How much PTO?',
    );
    expect(repository.insertMessage).toHaveBeenNthCalledWith(
      2,
      'session-1',
      'assistant',
      'You get 25 days [ab12cd34-0].',
      [citation],
    );
    const final = events.at(-1)!.data as { message: { id: string } };
    expect(final.message.id).toBe('msg-2');
  });

  it('backfills the run→message link when the final event lands (ADR-0005)', async () => {
    const { service, repository } = build();

    await collect(service.sendMessageStream('session-1', 'PTO?'));

    expect(repository.linkRunToMessage).toHaveBeenCalledWith('run-1', 'msg-2');
  });

  it('refuses sessions outside the tenant/user scope before storing anything', async () => {
    const { service, repository, agent } = build();
    repository.findSession.mockResolvedValue(undefined);

    await expect(collect(service.sendMessageStream('foreign', 'hi'))).rejects.toThrow(
      NotFoundException,
    );
    expect(repository.insertMessage).not.toHaveBeenCalled();
    expect(agent.answerStream).not.toHaveBeenCalled();
  });

  it('non-streaming variant resolves user and assistant rows', async () => {
    const { service } = build();

    const result = await service.sendMessage('session-1', 'PTO?');

    expect(result.user.role).toBe('user');
    expect(result.assistant.content).toBe('You get 25 days [ab12cd34-0].');
  });

  it('non-streaming variant fails loudly when the stream ends without a final', async () => {
    const { service } = build([{ event: 'run_start', data: { run_id: 'run-1' } }]);

    await expect(service.sendMessage('session-1', 'PTO?')).rejects.toThrow(BadGatewayException);
  });

  it('defaults blank titles when creating sessions', async () => {
    const { service, repository } = build();

    await service.createSession('   ');

    expect(repository.createSession).toHaveBeenCalledWith('tenant-1', 'user-1', 'New session');
  });
});
