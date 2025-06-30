'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/app/contexts/AuthContext'
import { 
  X, 
  Download, 
  FileText, 
  Image as ImageIcon, 
  File,
  Loader2,
  AlertCircle,
  ZoomIn,
  ZoomOut,
  RotateCw
} from 'lucide-react'

interface DocumentViewerProps {
  fileHash: string
  filename: string
  contentType: string
  fileSize: number
  onClose: () => void
}

export default function DocumentViewer({ 
  fileHash, 
  filename, 
  contentType, 
  fileSize,
  onClose 
}: DocumentViewerProps) {
  const { isLoggedIn } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fileUrl, setFileUrl] = useState<string | null>(null)
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)

  useEffect(() => {
    if (isLoggedIn && fileHash) {
      loadFileForViewing()
    }
  }, [fileHash, isLoggedIn])

  const loadFileForViewing = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`/api/backend/upload/download/${fileHash}`, {
        responseType: 'blob'
      })

      const blob = new Blob([response.data], { type: contentType })
      const url = URL.createObjectURL(blob)
      
      setFileUrl(url)
      setLoading(false)
    } catch (err: any) {
      setError(`Failed to load file: ${err.response?.data?.detail || err.message}`)
      setLoading(false)
    }
  }

  const downloadFile = async () => {
    try {
      const response = await axios.get(`/api/backend/upload/download/${fileHash}`, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(`Download failed: ${err.response?.data?.detail || err.message}`)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = () => {
    if (contentType.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />
    if (contentType.includes('image')) return <ImageIcon className="w-5 h-5 text-blue-500" />
    if (contentType.includes('text')) return <FileText className="w-5 h-5 text-green-500" />
    return <File className="w-5 h-5 text-gray-500" />
  }

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-gray-600">Loading document...</p>
        </div>
      )
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-96">
          <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
          <p className="text-red-600 text-center mb-4">{error}</p>
          <button
            onClick={loadFileForViewing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      )
    }

    if (!fileUrl) {
      return (
        <div className="flex flex-col items-center justify-center h-96">
          <File className="w-16 h-16 text-gray-400 mb-4" />
          <p className="text-gray-600">No content available</p>
        </div>
      )
    }

    // PDF files
    if (contentType.includes('pdf')) {
      return (
        <div className="w-full h-full">
          <iframe
            src={fileUrl}
            className="w-full h-96 border-0 rounded-lg"
            title={filename}
          />
        </div>
      )
    }

    // Image files
    if (contentType.includes('image')) {
      return (
        <div className="flex justify-center items-center p-4">
          <img
            src={fileUrl}
            alt={filename}
            className="max-w-full max-h-96 object-contain rounded-lg shadow-lg"
            style={{
              transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
              transition: 'transform 0.2s ease-in-out'
            }}
          />
        </div>
      )
    }

    // Text files
    if (contentType.includes('text') || contentType.includes('json') || contentType.includes('xml')) {
      return (
        <div className="w-full h-96 overflow-auto">
          <iframe
            src={fileUrl}
            className="w-full h-full border-0 rounded-lg bg-white"
            title={filename}
          />
        </div>
      )
    }

    // Default fallback for other file types
    return (
      <div className="flex flex-col items-center justify-center h-96">
        {getFileIcon()}
        <p className="text-gray-600 mt-4 text-center">
          Preview not available for this file type.
          <br />
          <span className="text-sm text-gray-500">You can download the file to view it.</span>
        </p>
      </div>
    )
  }

  const showZoomControls = contentType.includes('image')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] w-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            {getFileIcon()}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 truncate max-w-md">
                {filename}
              </h3>
              <p className="text-sm text-gray-500">
                {contentType} • {formatFileSize(fileSize)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {showZoomControls && (
              <>
                <button
                  onClick={() => setZoom(Math.max(zoom - 25, 25))}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-600 px-2">
                  {zoom}%
                </span>
                <button
                  onClick={() => setZoom(Math.min(zoom + 25, 300))}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setRotation((rotation + 90) % 360)}
                  className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                  title="Rotate"
                >
                  <RotateCw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => { setZoom(100); setRotation(0) }}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
                >
                  Reset
                </button>
                <div className="w-px h-6 bg-gray-300 mx-2" />
              </>
            )}
            
            <button
              onClick={downloadFile}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              title="Download"
            >
              <Download className="w-4 h-4" />
            </button>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {renderContent()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-sm text-gray-600">
            File Hash: <span className="font-mono">{fileHash.substring(0, 16)}...</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={downloadFile}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Cleanup function to revoke object URLs
export const cleanupDocumentViewer = () => {
  // This would be called when the component unmounts
  // Object URLs are automatically cleaned up by the browser, but we can do it explicitly
} 