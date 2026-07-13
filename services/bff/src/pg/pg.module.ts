import { Global, Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Pool } from 'pg';

export const PG_POOL = 'PG_POOL';

@Global()
@Module({
  providers: [
    {
      provide: PG_POOL,
      inject: [ConfigService],
      useFactory: (config: ConfigService): Pool =>
        new Pool({
          connectionString: config.get<string>(
            'DATABASE_URL',
            'postgres://scriptorium:scriptorium-dev@localhost:5432/scriptorium',
          ),
          max: 10,
        }),
    },
  ],
  exports: [PG_POOL],
})
export class PgModule {}
