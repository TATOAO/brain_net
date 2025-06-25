'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/app/contexts/AuthContext'
import Header from '@/app/components/Header'
import { 
  Upload, 
  File, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  MessageSquare,
  FileText,
  Hash,
  List,
  Download
} from 'lucide-react'

interface UploadResponse {
  status: string
  message: string
  file_hash: string
  filename: string
  file_size: number
  upload_time?: string
}

interface ProcessResponse {
  message: string
  status: string
  file_hash: string
  filename: string
  file_info?: any
  processing: string
}

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

export default function DocQA() {
  const { user, isLoggedIn } = useAuth()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [processResult, setProcessResult] = useState<ProcessResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recentFiles, setRecentFiles] = useState<UserFile[]>([])
  const [loadingFiles, setLoadingFiles] = useState(false)

  const loadRecentFiles = async () => {
    setLoadingFiles(true)
    try {
      const response = await axios.get<FileListResponse>('/api/backend/upload/my-files', {
        params: { limit: 5, offset: 0 }
      })
      setRecentFiles(response.data.files)
    } catch (err: any) {
      console.error('Failed to load recent files:', err)
    } finally {
      setLoadingFiles(false)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setUploadResult(null)
      setProcessResult(null)
      setError(null)
    }
  }

  const downloadFile = async (fileHash: string, filename: string) => {
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

  // Load recent files on component mount and after successful upload
  useEffect(() => {
    if (isLoggedIn) {
      loadRecentFiles()
    }
  }, [isLoggedIn])

  useEffect(() => {
    if (uploadResult) {
      loadRecentFiles() // Refresh file list after upload
    }
  }, [uploadResult])

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Upload to backend
      const uploadResponse = await axios.post('/api/backend/upload/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadResult(uploadResponse.data)
      
      // Automatically process the document
      await handleProcess(uploadResponse.data)

    } catch (err: any) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`)
      console.error('Upload error:', err)
    } finally {
      setUploading(false)
    }
  }

  const handleProcess = async (uploadData?: UploadResponse) => {
    const dataToUse = uploadData || uploadResult
    if (!dataToUse) {
      setError('No uploaded file to process')
      return
    }

    setProcessing(true)
    setError(null)

    try {
      // Send to backend for processing
      const processResponse = await axios.post('/api/backend/upload/process', {
        file_hash: dataToUse.file_hash,
        filename: dataToUse.filename
      })

      setProcessResult(processResponse.data)

    } catch (err: any) {
      setError(`Processing failed: ${err.response?.data?.detail || err.message}`)
      console.error('Processing error:', err)
    } finally {
      setProcessing(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'already_uploaded':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />
      case 'document_loaded':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'document_not_found':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <File className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded':
      case 'document_loaded':
        return 'text-green-800 bg-green-50 border-green-200'
      case 'already_uploaded':
        return 'text-yellow-800 bg-yellow-50 border-yellow-200'
      case 'document_not_found':
        return 'text-red-800 bg-red-50 border-red-200'
      default:
        return 'text-gray-800 bg-gray-50 border-gray-200'
    }
  }

  // Redirect to login if not authenticated
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Access Restricted</h1>
            <p className="text-gray-600 mb-8">Please log in to access the Document Q&A system.</p>
            <a
              href="/login"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Sign In
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Document Q&A</h1>
          <p className="text-gray-600">Upload documents and interact with them using AI-powered Q&A.</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Upload className="w-5 h-5 mr-2" />
              Upload Document
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  accept=".pdf,.docx,.txt,.md,.html,.csv,.json"
                />
              </div>

              {selectedFile && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium">{selectedFile.name}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Size: {formatFileSize(selectedFile.size)}
                  </div>
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload & Process
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <MessageSquare className="w-5 h-5 mr-2" />
              Results
            </h2>

            <div className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <XCircle className="w-5 h-5 text-red-600" />
                    <span className="text-red-800 font-medium">Error</span>
                  </div>
                  <p className="text-red-700 text-sm mt-1">{error}</p>
                </div>
              )}

              {uploadResult && (
                <div className={`border rounded-lg p-4 ${getStatusColor(uploadResult.status)}`}>
                  <div className="flex items-center space-x-2 mb-2">
                    {getStatusIcon(uploadResult.status)}
                    <span className="font-medium">Upload Status</span>
                  </div>
                  <p className="text-sm mb-2">{uploadResult.message}</p>
                  <div className="text-xs space-y-1">
                    <div className="flex items-center space-x-2">
                      <Hash className="w-3 h-3" />
                      <span>Hash: {uploadResult.file_hash}</span>
                    </div>
                    <div>File: {uploadResult.filename}</div>
                    {uploadResult.file_size > 0 && (
                      <div>Size: {formatFileSize(uploadResult.file_size)}</div>
                    )}
                    {uploadResult.upload_time && (
                      <div>Uploaded: {new Date(uploadResult.upload_time).toLocaleString()}</div>
                    )}
                  </div>
                </div>
              )}

              {processing && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
                    <span className="text-blue-800 font-medium">Processing Document...</span>
                  </div>
                  <p className="text-blue-700 text-sm mt-1">Sending to LLM service for analysis</p>
                </div>
              )}

              {processResult && (
                <div className={`border rounded-lg p-4 ${getStatusColor(processResult.status)}`}>
                  <div className="flex items-center space-x-2 mb-2">
                    {getStatusIcon(processResult.status)}
                    <span className="font-medium">Processing Result</span>
                  </div>
                  <p className="text-lg font-semibold mb-2">{processResult.message}</p>
                  <p className="text-sm mb-2">{processResult.processing}</p>
                  <div className="text-xs space-y-1">
                    <div>Status: {processResult.status}</div>
                    <div>File: {processResult.filename}</div>
                    <div className="flex items-center space-x-2">
                      <Hash className="w-3 h-3" />
                      <span>Hash: {processResult.file_hash}</span>
                    </div>
                  </div>
                </div>
              )}

              {!uploadResult && !processResult && !error && !uploading && !processing && (
                <div className="text-center text-gray-500 py-8">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Upload a document to get started</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Files Section */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <List className="w-5 h-5 mr-2" />
              Recent Files
            </h2>
            <button
              onClick={loadRecentFiles}
              disabled={loadingFiles}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${loadingFiles ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {loadingFiles ? (
            <div className="text-center py-4">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Loading files...</p>
            </div>
          ) : recentFiles.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <File className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No files uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentFiles.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-5 h-5 text-blue-500" />
                    <div>
                      <div className="font-medium text-sm">{file.original_filename}</div>
                      <div className="text-xs text-gray-500">
                        {formatFileSize(file.file_size)} • {new Date(file.uploaded_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => downloadFile(file.file_hash, file.original_filename)}
                      className="text-blue-600 hover:text-blue-800 p-1"
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <span className="text-xs text-gray-400 font-mono">
                      {file.file_hash.substring(0, 8)}...
                    </span>
                  </div>
                </div>
              ))}
              {recentFiles.length >= 5 && (
                <div className="text-center">
                  <a
                    href="/files"
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View all files →
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Information Section */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Upload className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold mb-2">1. Upload</h3>
              <p className="text-sm text-gray-600">Select and upload your document. Files are stored securely in MinIO.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <RefreshCw className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold mb-2">2. Process</h3>
              <p className="text-sm text-gray-600">Document is sent to our LLM service for analysis and processing.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <MessageSquare className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold mb-2">3. Q&A Ready</h3>
              <p className="text-sm text-gray-600">Once processed, you can ask questions about your document content.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 