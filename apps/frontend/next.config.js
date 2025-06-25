/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use internal API URL for server-side requests within Docker network
    // Fall back to NEXT_PUBLIC_API_URL for development outside Docker
    const apiUrl = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    return [
      {
        source: '/api/backend/health/:path*',
        destination: `${apiUrl}/health/:path*`
      },
      {
        source: '/api/backend/:path*',
        destination: `${apiUrl}/api/v1/:path*`
      }
    ]
  }
}

module.exports = nextConfig 