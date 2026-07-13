import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import cookieParser from 'cookie-parser';

import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
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
