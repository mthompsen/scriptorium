import { Body, Controller, Get, Post, Req, Res, UseGuards } from '@nestjs/common';
import type { Response } from 'express';

import { AuthService, LoginResult } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { ACCESS_TOKEN_COOKIE, JwtAuthGuard } from './jwt-auth.guard';
import type { AuthenticatedRequest, Principal } from './principal';

const COOKIE_MAX_AGE_MS = 30 * 60 * 1000; // matches JWT expiry

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login')
  async login(
    @Body() dto: LoginDto,
    @Res({ passthrough: true }) res: Response,
  ): Promise<LoginResult> {
    const result = await this.authService.login(dto.email, dto.password);
    // HttpOnly cookie for the browser flow (ADR-0003); token also returned
    // in the body for non-browser clients.
    res.cookie(ACCESS_TOKEN_COOKIE, result.accessToken, {
      httpOnly: true,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
      maxAge: COOKIE_MAX_AGE_MS,
    });
    return result;
  }

  @Post('logout')
  logout(@Res({ passthrough: true }) res: Response): { ok: true } {
    res.clearCookie(ACCESS_TOKEN_COOKIE);
    return { ok: true };
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  me(@Req() req: AuthenticatedRequest): Principal {
    return req.principal;
  }
}
