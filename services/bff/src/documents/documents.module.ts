import { Module } from '@nestjs/common';

import { AuthModule } from '../auth/auth.module';
import { DocumentsController } from './documents.controller';
import { DocumentsRepository } from './documents.repository';
import { DocumentsService } from './documents.service';
import { IngestionClient } from './ingestion.client';

@Module({
  imports: [AuthModule],
  controllers: [DocumentsController],
  providers: [DocumentsService, DocumentsRepository, IngestionClient],
})
export class DocumentsModule {}
