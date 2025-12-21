import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SPIRAL - Multi-Hazard Prediction System',
  description: 'Structured Physics-Informed Representation-Augmented Learning from Atmospheric Gravity Wave Signals for Multi-Hazard Prediction in India and Real-Time Web and Mobile Risk Alerts',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
