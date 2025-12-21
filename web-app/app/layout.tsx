import type { Metadata } from 'next'
import './globals.css'

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
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
