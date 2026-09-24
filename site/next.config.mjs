import { PHASE_DEVELOPMENT_SERVER } from 'next/constants.js'

const basePath = process.env.PAGES_BASE_PATH ?? '/phaser-design'

/** @type {(phase: string) => import('next').NextConfig} */
export default (phase) => ({
  output: 'export',
  basePath,
  assetPrefix: basePath,
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
  env: { NEXT_PUBLIC_BASE_PATH: basePath },
  outputFileTracingRoot: import.meta.dirname,
  // dev server gets its own build dir, so `next build` can run alongside it without clobbering its chunks
  distDir: phase === PHASE_DEVELOPMENT_SERVER ? '.next-dev' : '.next',
})
