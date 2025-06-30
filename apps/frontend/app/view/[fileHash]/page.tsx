'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import axios from 'axios'
import { useAuth } from '@/app/contexts/AuthContext'
import Header from '@/app/components/Header'
import DocumentViewer from '@/app/components/DocumentViewer'
import { Loader2, AlertCircle } from 'lucide-react'

interface FileInfo {
  id: number
  file_hash: string
  original_filename: string
  file_size: number
  content_type: string
  uploaded_at: string
}

export default function ViewDocumentPage() {
  const { fileHash } = useParams()
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isLoggedIn && fileHash) {
      loadFileInfo()
    } else if (!isLoggedIn) {
      setLoading(false)
    }
  }, [fileHash, isLoggedIn])

  const loadFileInfo = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`/api/backend/upload/info/${fileHash}`)
      setFileInfo(response.data)
    } catch (err: any) {
      setError(`Failed to load file info: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    router.push('/files')
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600">Please log in to view documents.</p>
          </div>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
            <p className="text-gray-600">Loading document...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !fileInfo) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Document Not Found</h2>
            <p className="text-red-600 text-center mb-4">
              {error || 'The requested document could not be found or you do not have access to it.'}
            </p>
            <button
              onClick={() => router.push('/files')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to My Files
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <DocumentViewer
        fileHash={fileInfo.file_hash}
        filename={fileInfo.original_filename}
        contentType={fileInfo.content_type}
        fileSize={fileInfo.file_size}
        onClose={handleClose}
      />
    </div>
  )
} 