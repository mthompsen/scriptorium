import { Controller, Get } from '@nestjs/common';
import { SkipThrottle } from '@nestjs/throttler';

export interface HealthStatus {
  status: 'ok';
  service: 'bff';
}

// Infra probes (docker/k8s healthchecks) must never consume the rate budget.
@SkipThrottle()
@Controller('health')
export class HealthController {
  @Get()
  health(): HealthStatus {
    return { status: 'ok', service: 'bff' };
  }
}
