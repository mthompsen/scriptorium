import { BadGatewayException, NotFoundException } from '@nestjs/common';

import type { TenantContext } from '../auth/tenant-context';
import type { AgentClient } from './agent.client';
import type { ChatRepository } from './chat.repository';
import { ChatService } from './chat.service';

const tenant = { tenantId: 'tenant-1', userId: 'user-1' } as TenantContext;
const session = { id: 'session-1', tenant_id: 'tenant-1', user_id: 'user-1' };

const citation = { chunk_id: 'ab12cd34-0', document_id: 'doc-1', snippet: 'PTO is 25 days.' };

const build = () => {
  const repository = {
    createSession: jest.fn().mockResolvedValue(session),
    listSessions: jest.fn().mockResolvedValue([session]),
    findSession: jest.fn().mockResolvedValue(session),
    insertMessage: jest
      .fn()
      .mockImplementation(
        (sessionId: string, role: string, content: string, citations: unknown[] = []) =>
          Promise.resolve({ id: `${role}-msg`, session_id: sessionId, role, content, citations }),
      ),
    listMessages: jest.fn().mockResolvedValue([]),
  };
  const agent = {
    answer: jest.fn().mockResolvedValue({
      answer: 'You get 25 days of PTO [ab12cd34-0].',
      citations: [citation],
      grounded: true,
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

describe('ChatService', () => {
  it('stores the user message and the grounded agent answer with citations', async () => {
    const { service, repository, agent } = build();

    const result = await service.sendMessage('session-1', 'How much PTO do I get?');

    expect(agent.answer).toHaveBeenCalledWith('tenant-1', 'How much PTO do I get?');
    expect(repository.insertMessage).toHaveBeenNthCalledWith(
      1,
      'session-1',
      'user',
      'How much PTO do I get?',
    );
    expect(repository.insertMessage).toHaveBeenNthCalledWith(
      2,
      'session-1',
      'assistant',
      'You get 25 days of PTO [ab12cd34-0].',
      [citation],
    );
    expect(result.assistant.citations).toEqual([citation]);
  });

  it('propagates agent unavailability after storing the user message', async () => {
    const { service, repository, agent } = build();
    agent.answer.mockRejectedValue(new BadGatewayException('Agent service unavailable'));

    await expect(service.sendMessage('session-1', 'hello there')).rejects.toThrow(
      BadGatewayException,
    );
    expect(repository.insertMessage).toHaveBeenCalledTimes(1); // user message only
  });

  it('refuses messages to sessions outside the tenant/user scope', async () => {
    const { service, repository, agent } = build();
    repository.findSession.mockResolvedValue(undefined);

    await expect(service.sendMessage('foreign-session', 'hi there')).rejects.toThrow(
      NotFoundException,
    );
    expect(agent.answer).not.toHaveBeenCalled();
    expect(repository.findSession).toHaveBeenCalledWith('tenant-1', 'user-1', 'foreign-session');
  });

  it('defaults blank titles when creating sessions', async () => {
    const { service, repository } = build();

    await service.createSession('   ');

    expect(repository.createSession).toHaveBeenCalledWith('tenant-1', 'user-1', 'New session');
  });
});
