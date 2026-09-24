import type { Metadata, Viewport } from 'next'
import { Archivo, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'

const display = Archivo({ subsets: ['latin'], axes: ['wdth'], variable: '--f-display', display: 'swap' })
const mono = IBM_Plex_Mono({ subsets: ['latin'], weight: ['400', '500'], variable: '--f-mono', display: 'swap' })

export const metadata: Metadata = {
  metadataBase: new URL('https://jacobfv.github.io/phaser-design/'),
  title: 'PHASER — compute with light',
  description: 'Light bouncing between two mirrors, computing on every pass. Modeled at one megapixel: about 1,000× less energy per step than a GPU.',
  openGraph: { title: 'PHASER — compute with light', description: '~1,000× less energy per step than a GPU (modeled). Every bounce of light is a computation.', images: ['og.jpg'] },
  twitter: { card: 'summary_large_image', title: 'PHASER — compute with light', description: '~1,000× less energy per step than a GPU (modeled).', images: ['og.jpg'] },
}

export const viewport: Viewport = { themeColor: '#0a0908', colorScheme: 'dark' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
