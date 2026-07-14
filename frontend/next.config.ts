import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Standalone output keeps the Docker runtime image minimal (ARCHITECTURE.md Section 14.2).
  output: 'standalone',
};

export default nextConfig;
