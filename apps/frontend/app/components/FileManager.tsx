'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/app/contexts/AuthContext'
import { 
  File, 
  Download, 
  Trash2, 
  RefreshCw,
  FileText,
  Hash,
  Calendar,
  HardDrive
} from 'lucide-react'

interface UserFile {
  id: number
  file_hash: string
  original_filename: string
  file_size: number
  content_type: string
  uploaded_at: string
}

interface FileListResponse {
  files: UserFile[]
  total_count: number
}

export default function FileManager() {
  const { user, isLoggedIn } = useAuth()
  const [files, setFiles] = useState<UserFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)

  const loadFiles = async () => {
    if (!isLoggedIn) return

    setLoading(true)
    setError(null)

    try {
      const response = await axios.get<FileListResponse>('/api/backend/upload/my-files', {
        params: { limit: 100, offset: 0 }
      })

      setFiles(response.data.files)
      setTotalCount(response.data.total_count)
    } catch (err: any) {
      setError(`Failed to load files: ${err.response?.data?.detail || err.message}`)
      console.error('Load files error:', err)
    } finally {
      setLoading(false)
    }
  }

  const downloadFile = async (fileHash: string, filename: string) => {
    try {
      const response = await axios.get(`/api/backend/upload/download/${fileHash}`, {
        responseType: 'blob'
      })

      // Create download link
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
      console.error('Download error:', err)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString()
  }

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return <FileText className="w-5 h-5 text-red-500" />
    if (contentType.includes('image')) return <File className="w-5 h-5 text-blue-500" />
    if (contentType.includes('text')) return <FileText className="w-5 h-5 text-green-500" />
    return <File className="w-5 h-5 text-gray-500" />
  }

  useEffect(() => {
    loadFiles()
  }, [isLoggedIn])

  if (!isLoggedIn) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Please log in to view your files.</p>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Files</h1>
        <button
          onClick={loadFiles}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading your files...</p>
        </div>
      ) : files.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <File className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No files yet</h3>
          <p className="text-gray-600">Upload your first file to get started!</p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-600">
            Showing {files.length} of {totalCount} files
          </div>
          
          <div className="bg-white shadow-sm rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Uploaded
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hash
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {files.map((file) => (
                    <tr key={file.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getFileIcon(file.content_type)}
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              {file.original_filename}
                            </div>
                            <div className="text-sm text-gray-500">
                              {file.content_type}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-900">
                          <HardDrive className="w-4 h-4 mr-1" />
                          {formatFileSize(file.file_size)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-900">
                          <Calendar className="w-4 h-4 mr-1" />
                          {formatDate(file.uploaded_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-xs font-mono text-gray-500">
                          <Hash className="w-3 h-3 mr-1" />
                          {file.file_hash.substring(0, 8)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => downloadFile(file.file_hash, file.original_filename)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Download file"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
} 