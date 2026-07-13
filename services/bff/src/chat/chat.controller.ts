import { Body, Controller, Get, Param, ParseUUIDPipe, Post, UseGuards } from '@nestjs/common';

import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ChatMessageRow, ChatSessionRow } from './chat.repository';
import { ChatService } from './chat.service';
import { CreateSessionDto, SendMessageDto } from './dto/chat.dto';

@Controller('chat/sessions')
@UseGuards(JwtAuthGuard)
export class ChatController {
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
  sendMessage(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: SendMessageDto,
  ): Promise<{ user: ChatMessageRow; assistant: ChatMessageRow }> {
    return this.chat.sendMessage(id, dto.content);
  }

  @Get(':id/messages')
  listMessages(@Param('id', ParseUUIDPipe) id: string): Promise<ChatMessageRow[]> {
    return this.chat.listMessages(id);
  }
}
