import {
  BadRequestException,
  Controller,
  DefaultValuePipe,
  Get,
  Param,
  ParseIntPipe,
  ParseUUIDPipe,
  Post,
  Query,
  UploadedFile,
  UseGuards,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';

import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { DocumentRow } from './documents.repository';
import { DocumentsService, UploadedFile as Upload } from './documents.service';

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024; // request size limit (Section 12)

@Controller('documents')
@UseGuards(JwtAuthGuard)
export class DocumentsController {
  constructor(private readonly documents: DocumentsService) {}

  @Get()
  list(
    @Query('limit', new DefaultValuePipe(20), ParseIntPipe) limit: number,
    @Query('offset', new DefaultValuePipe(0), ParseIntPipe) offset: number,
  ): Promise<DocumentRow[]> {
    return this.documents.list(limit, offset);
  }

  @Post()
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: MAX_UPLOAD_BYTES } }))
  upload(@UploadedFile() file?: Upload): Promise<DocumentRow> {
    if (!file) {
      throw new BadRequestException('Multipart field "file" is required');
    }
    return this.documents.upload(file);
  }

  @Get(':id/status')
  status(
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<{ id: string; status: string; indexedAt: string | null }> {
    return this.documents.status(id);
  }
}
