import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

import { AuthModule } from './auth/auth.module';
import { ChatModule } from './chat/chat.module';
import { DocumentsModule } from './documents/documents.module';
import { HealthController } from './health/health.controller';
import { PgModule } from './pg/pg.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PgModule,
    AuthModule,
    DocumentsModule,
    ChatModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
