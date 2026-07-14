import { Module } from '@nestjs/common';

import { AuthModule } from '../auth/auth.module';
import { GraphController } from './graph.controller';
import { RetrievalGraphClient } from './retrieval-graph.client';

@Module({
  imports: [AuthModule],
  controllers: [GraphController],
  providers: [RetrievalGraphClient],
})
export class GraphModule {}
