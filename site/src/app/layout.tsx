import type { Metadata, Viewport } from 'next'
import { Archivo, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'

const display = Archivo({ subsets: ['latin'], axes: ['wdth'], variable: '--f-display', display: 'swap' })
const mono = IBM_Plex_Mono({ subsets: ['latin'], weight: ['400', '500'], variable: '--f-mono', display: 'swap' })

export const metadata: Metadata = {
  metadataBase: new URL('https://jacobfv.github.io/phaser-design/'),
  title: 'PHASER — a neural accelerator that runs at the speed of light',
  description: 'A neural accelerator that runs at the speed of light, designed around parts the telecom and display industries already make by the million.',
  openGraph: { title: 'PHASER — a neural accelerator that runs at the speed of light', description: 'A neural accelerator that runs at the speed of light. No new fabs, no exotic materials, no new power plants.', images: ['og.jpg'] },
  twitter: { card: 'summary_large_image', title: 'PHASER — a neural accelerator that runs at the speed of light', description: 'A neural accelerator that runs at the speed of light.', images: ['og.jpg'] },
}

export const viewport: Viewport = { themeColor: '#0a0908', colorScheme: 'dark' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body>
        <div className="ground" aria-hidden="true" />
        {children}
      </body>
    </html>
  )
}
