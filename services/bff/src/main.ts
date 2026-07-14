import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import cookieParser from 'cookie-parser';
import helmet from 'helmet';

import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  // Security headers at the edge (Section 12): CSP, HSTS, X-Frame-Options,
  // X-Content-Type-Options: nosniff, Referrer-Policy, and removal of the
  // X-Powered-By: Express banner. Defaults are safe for this JSON/SSE API —
  // no HTML is served here, so the default CSP does not affect the SPA
  // (a separate origin), and CORS-enabled fetches are unaffected by the
  // same-origin CORP default.
  app.use(helmet());
  app.use(cookieParser());
  // Reject unknown fields at the edge (input validation, Section 12).
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true }));
  app.enableCors({
    origin: process.env.FRONTEND_ORIGIN ?? 'http://localhost:3000',
    credentials: true,
  });
  app.setGlobalPrefix('api/v1', { exclude: ['health'] });
  await app.listen(Number(process.env.PORT ?? 3001), '0.0.0.0');
}

void bootstrap();
