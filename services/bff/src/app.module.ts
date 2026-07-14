import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { APP_GUARD } from '@nestjs/core';
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';

import { AuthModule } from './auth/auth.module';
import { ChatModule } from './chat/chat.module';
import { DocumentsModule } from './documents/documents.module';
import { GraphModule } from './graph/graph.module';
import { HealthController } from './health/health.controller';
import { PgModule } from './pg/pg.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    // Rate limiting (Section 12). The 'default' bucket is a generous
    // per-IP ceiling; tighter per-route limits (e.g. login) are applied
    // with @Throttle on the handler. The long-lived chat SSE POST counts
    // as one request on arrival, so streaming is unaffected.
    ThrottlerModule.forRoot([{ name: 'default', ttl: 60_000, limit: 120 }]),
    PgModule,
    AuthModule,
    DocumentsModule,
    ChatModule,
    GraphModule,
  ],
  controllers: [HealthController],
  providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }],
})
export class AppModule {}
