import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import Script from 'next/script'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Chatflow Tailor',
  description: 'Claude Agent for Workflow Generation - 将自然语言转换为 Agent Studio Chatflow',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="zh-CN">
        <body className={inter.className}>
          {children}
          <Script
            src="https://human-hand-off.up.railway.app/widget.js"
            data-agent-url="https://human-hand-off.up.railway.app"
            strategy="lazyOnload"
          />
        </body>
      </html>
    </ClerkProvider>
  )
}
