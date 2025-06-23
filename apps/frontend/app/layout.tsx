import React from 'react'
import './globals.css'
import type { Metadata } from 'next'
import { AuthProvider } from '@/app/contexts/AuthContext'

export const metadata: Metadata = {
  title: 'Brain Net - Intelligent Knowledge Management',
  description: 'An intelligent and highly visualized RAG system for local knowledge base management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
} 