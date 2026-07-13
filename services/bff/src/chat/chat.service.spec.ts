import { NotFoundException } from '@nestjs/common';

import type { TenantContext } from '../auth/tenant-context';
import type { ChatRepository } from './chat.repository';
import { ChatService } from './chat.service';

const tenant = { tenantId: 'tenant-1', userId: 'user-1' } as TenantContext;
const session = { id: 'session-1', tenant_id: 'tenant-1', user_id: 'user-1' };

const build = () => {
  const repository = {
    createSession: jest.fn().mockResolvedValue(session),
    listSessions: jest.fn().mockResolvedValue([session]),
    findSession: jest.fn().mockResolvedValue(session),
    insertMessage: jest
      .fn()
      .mockImplementation((sessionId: string, role: string, content: string) =>
        Promise.resolve({ id: `${role}-msg`, session_id: sessionId, role, content }),
      ),
    listMessages: jest.fn().mockResolvedValue([]),
  };
  return {
    repository,
    service: new ChatService(tenant, repository as unknown as ChatRepository),
  };
};

describe('ChatService', () => {
  it('stores the user message and an assistant echo clearly marked as a stub', async () => {
    const { service, repository } = build();

    const result = await service.sendMessage('session-1', 'What is our leave policy?');

    expect(repository.insertMessage).toHaveBeenNthCalledWith(
      1,
      'session-1',
      'user',
      'What is our leave policy?',
    );
    expect(result.assistant.content).toContain('stub');
    expect(result.assistant.content).toContain('What is our leave policy?');
  });

  it('refuses messages to sessions outside the tenant/user scope', async () => {
    const { service, repository } = build();
    repository.findSession.mockResolvedValue(undefined);

    await expect(service.sendMessage('foreign-session', 'hi there')).rejects.toThrow(
      NotFoundException,
    );
    expect(repository.insertMessage).not.toHaveBeenCalled();
    expect(repository.findSession).toHaveBeenCalledWith('tenant-1', 'user-1', 'foreign-session');
  });

  it('defaults blank titles when creating sessions', async () => {
    const { service, repository } = build();

    await service.createSession('   ');

    expect(repository.createSession).toHaveBeenCalledWith('tenant-1', 'user-1', 'New session');
  });
});
