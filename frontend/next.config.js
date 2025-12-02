/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // 生产环境使用 Railway 后端，开发环境使用本地
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/backend/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
