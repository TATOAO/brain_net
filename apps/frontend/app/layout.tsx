import React from 'react'
import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Brain Net - Health Dashboard',
  description: 'Health monitoring dashboard for Brain Net services',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Brain Net Health Dashboard
            </h1>
            <p className="text-gray-600">
              Monitor the health status of all Brain Net backend services
            </p>
          </header>
          {children}
        </div>
      </body>
    </html>
  )
} 