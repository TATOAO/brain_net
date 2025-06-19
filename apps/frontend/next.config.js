/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use environment variable for API URL, fallback to localhost for development
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    return [
      {
        source: '/api/backend/:path*',
        destination: `${apiUrl}/:path*`
      }
    ]
  }
}

module.exports = nextConfig 