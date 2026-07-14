import type { NextConfig } from 'next';

// Headers that cost nothing here — no script-src CSP, so pages stay
// statically prerendered (a nonce-based script CSP would force dynamic
// rendering; 'unsafe-inline' would not be a real CSP). The CSP below is
// frame-ancestors only: framing protection without touching scripts.
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
];

const nextConfig: NextConfig = {
  // Standalone output keeps the Docker runtime image minimal (ARCHITECTURE.md Section 14.2).
  output: 'standalone',
  // Drop the X-Powered-By: Next.js banner.
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }];
  },
};

export default nextConfig;
