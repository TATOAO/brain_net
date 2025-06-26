'use client'

import React from 'react'
import { useAuth } from '@/app/contexts/AuthContext'
import Header from '@/app/components/Header'
import FileManager from '@/app/components/FileManager'

export default function FilesPage() {
  const { isLoggedIn } = useAuth()

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600">Please log in to access your files.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <FileManager />
      </div>
    </div>
  )
} 