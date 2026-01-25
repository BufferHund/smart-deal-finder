import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Support large file uploads (up to 50MB)
  experimental: {
    serverActions: {
      bodySizeLimit: '50mb',
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*', // Proxy to Backend
      },
    ];
  },
};

export default nextConfig;
