import { Controller, Get } from '@nestjs/common';

export interface HealthStatus {
  status: 'ok';
  service: 'bff';
}

@Controller('health')
export class HealthController {
  @Get()
  health(): HealthStatus {
    return { status: 'ok', service: 'bff' };
  }
}
