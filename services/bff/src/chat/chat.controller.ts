import {
  Body,
  Controller,
  Get,
  HttpException,
  Logger,
  Param,
  ParseUUIDPipe,
  Post,
  Query,
  Res,
  UseGuards,
} from '@nestjs/common';
import type { Response } from 'express';

import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ChatMessageRow, ChatSessionRow } from './chat.repository';
import { ChatService } from './chat.service';
import { CreateSessionDto, SendMessageDto } from './dto/chat.dto';

@Controller('chat/sessions')
@UseGuards(JwtAuthGuard)
export class ChatController {
  private readonly logger = new Logger(ChatController.name);

  constructor(private readonly chat: ChatService) {}

  @Post()
  createSession(@Body() dto: CreateSessionDto): Promise<ChatSessionRow> {
    return this.chat.createSession(dto.title);
  }

  @Get()
  listSessions(): Promise<ChatSessionRow[]> {
    return this.chat.listSessions();
  }

  @Post(':id/messages')
  async sendMessage(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: SendMessageDto,
    @Res() res: Response,
    @Query('stream') stream?: string,
  ): Promise<void> {
    if (stream === 'false') {
      const result = await this.chat.sendMessage(id, dto.content);
      res.json(result);
      return;
    }
    // SSE over POST (ADR-0005): tokens and tool events reach the browser live.
    // The first event is awaited before headers flush so session/auth errors
    // still surface as proper HTTP error responses.
    const events = this.chat.sendMessageStream(id, dto.content);
    const first = await events.next();
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();
    const write = (event: { event: string; data: Record<string, unknown> }): void => {
      res.write(`event: ${event.event}\ndata: ${JSON.stringify(event.data)}\n\n`);
    };
    try {
      if (!first.done) {
        write(first.value);
        for await (const event of events) {
          write(event);
        }
      }
    } catch (error) {
      // Only surface our own HttpException messages (server-authored, safe
      // constants). Anything raised by library internals inside the
      // for-await — e.g. a JSON.parse SyntaxError echoing malformed,
      // LLM-influenced SSE frame content — is logged server-side and
      // reported as a generic constant, so no unbounded exception text
      // reaches the client.
      this.logger.error('chat stream failed', error instanceof Error ? error.stack : error);
      const message = error instanceof HttpException ? error.message : 'stream failed';
      res.write(`event: error\ndata: ${JSON.stringify({ message })}\n\n`);
    } finally {
      res.end();
    }
  }

  @Get(':id/messages')
  listMessages(@Param('id', ParseUUIDPipe) id: string): Promise<ChatMessageRow[]> {
    return this.chat.listMessages(id);
  }
}
