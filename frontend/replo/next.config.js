/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable standalone output for Docker production builds
  output: 'standalone',
  // Add custom config options here as needed
};

module.exports = nextConfig;
