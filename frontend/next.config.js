/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
  basePath: process.env.NODE_ENV === 'production' ? '/carlens-lk' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/carlens-lk/' : '',
}
module.exports = nextConfig