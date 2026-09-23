import type { Metadata, Viewport } from 'next'
import { Newsreader, Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const serif = Newsreader({ subsets: ['latin'], weight: ['300', '400'], style: ['normal', 'italic'], variable: '--f-serif', display: 'swap' })
const sans = Inter({ subsets: ['latin'], weight: ['400', '500'], variable: '--f-sans', display: 'swap' })
const mono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'], variable: '--f-mono', display: 'swap' })

export const metadata: Metadata = {
  title: 'PHASER — computation by round trip',
  description:
    'A recurrent free-space optical cavity where each 0.667 ns round trip of light is one compute step. Simulated research results, with every number linked to its source.',
}

export const viewport: Viewport = { themeColor: '#050608', colorScheme: 'dark' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
