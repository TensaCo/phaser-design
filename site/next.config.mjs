/** @type {import('next').NextConfig} */
const basePath = process.env.PAGES_BASE_PATH ?? '/phaser-design'
export default {
  output: 'export',
  basePath,
  assetPrefix: basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  outputFileTracingRoot: import.meta.dirname,
}
