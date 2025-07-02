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
  Download,
  Settings,
  Play,
  Edit,
  Plus,
  Trash2,
  GitBranch,
  Clock,
  Users,
  Activity
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

interface ProcessorStep {
  processor_id: number
  config: Record<string, any>
  order?: number
}

interface Pipeline {
  id: number
  name: string
  description: string
  status: 'active' | 'inactive' | 'running' | 'completed' | 'failed'
  processor_sequence: ProcessorStep[]
  execution_count: number
  last_executed?: string
  average_execution_time?: number
  created_at: string
  updated_at: string
}

interface PipelineListResponse {
  pipelines: Pipeline[]
  total_count: number
}

interface PipelineExecution {
  execution_id: string
  status: 'started' | 'running' | 'completed' | 'failed'
  pipeline_id: number
  file_hash: string
  started_at?: string
  completed_at?: string
  execution_time?: number
  error_details?: string
}

interface PipelineEditModal {
  isOpen: boolean
  pipeline: Pipeline | null
  mode: 'create' | 'edit'
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
  
  // Pipeline management state
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [loadingPipelines, setLoadingPipelines] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())
  const [pipelineExecutions, setPipelineExecutions] = useState<Record<string, PipelineExecution>>({})
  const [editModal, setEditModal] = useState<PipelineEditModal>({ isOpen: false, pipeline: null, mode: 'create' })
  const [pipelineForm, setPipelineForm] = useState({
    name: '',
    description: '',
    processor_sequence: [] as ProcessorStep[]
  })

  const loadRecentFiles = async () => {
    setLoadingFiles(true)
    try {
      const response = await axios.get<FileListResponse>('/api/backend/upload/my-files', {
        params: { limit: 10, offset: 0 }
      })
      setRecentFiles(response.data.files)
    } catch (err: any) {
      console.error('Failed to load recent files:', err)
    } finally {
      setLoadingFiles(false)
    }
  }

  const loadPipelines = async () => {
    setLoadingPipelines(true)
    try {
      const response = await axios.get<PipelineListResponse>('/api/backend/processors/pipelines', {
        params: { limit: 50, skip: 0 }
      })
      setPipelines(response.data.pipelines)
    } catch (err: any) {
      console.error('Failed to load pipelines:', err)
      // Mock data for development
      setPipelines([
        {
          id: 1,
          name: 'Document Analysis Pipeline',
          description: 'Comprehensive document analysis with chunking and entity extraction',
          status: 'active',
          processor_sequence: [
            { processor_id: 1, config: { chunk_size: 1000, overlap: 200 } },
            { processor_id: 2, config: { entity_types: ['PERSON', 'ORG', 'GPE'] } }
          ],
          execution_count: 15,
          last_executed: '2024-01-10T10:30:00Z',
          average_execution_time: 45.5,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-10T10:30:00Z'
        },
        {
          id: 2,
          name: 'Quick Text Processing',
          description: 'Fast text chunking for simple documents',
          status: 'active',
          processor_sequence: [
            { processor_id: 1, config: { chunk_size: 500, overlap: 100 } }
          ],
          execution_count: 8,
          last_executed: '2024-01-09T15:20:00Z',
          average_execution_time: 12.3,
          created_at: '2024-01-05T00:00:00Z',
          updated_at: '2024-01-09T15:20:00Z'
        }
      ])
    } finally {
      setLoadingPipelines(false)
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

  const handleFileCheckboxChange = (fileHash: string, checked: boolean) => {
    const newSelected = new Set(selectedFiles)
    if (checked) {
      newSelected.add(fileHash)
    } else {
      newSelected.delete(fileHash)
    }
    setSelectedFiles(newSelected)
  }

  const handleSelectAllFiles = (checked: boolean) => {
    if (checked) {
      setSelectedFiles(new Set(recentFiles.map(file => file.file_hash)))
    } else {
      setSelectedFiles(new Set())
    }
  }

  const executePipelineOnFiles = async (pipelineId: number, fileHashes: string[]) => {
    setError(null)
    
    try {
      const response = await axios.post('/api/backend/processors/batch-execute', {
        pipeline_id: pipelineId,
        file_hashes: fileHashes,
        custom_config: {}
      })

      // Update execution tracking
      const newExecutions = { ...pipelineExecutions }
      response.data.executions.forEach((exec: any) => {
        newExecutions[exec.execution_id] = {
          execution_id: exec.execution_id,
          status: exec.status,
          pipeline_id: pipelineId,
          file_hash: exec.file_hash,
          started_at: new Date().toISOString()
        }
      })
      setPipelineExecutions(newExecutions)

      // Show success message
      const successCount = response.data.successful_starts
      const totalCount = response.data.batch_size
      setProcessResult({
        message: `Pipeline execution started successfully`,
        status: 'started',
        file_hash: fileHashes.join(', '),
        filename: `${successCount}/${totalCount} files`,
        processing: `Started processing ${successCount} files with pipeline`
      })

    } catch (err: any) {
      setError(`Pipeline execution failed: ${err.response?.data?.detail || err.message}`)
      console.error('Pipeline execution error:', err)
    }
  }

  const handleExecutePipeline = async (pipelineId: number) => {
    if (selectedFiles.size === 0) {
      setError('Please select at least one file to process')
      return
    }

    await executePipelineOnFiles(pipelineId, Array.from(selectedFiles))
  }

  const handleEditPipeline = (pipeline: Pipeline) => {
    setPipelineForm({
      name: pipeline.name,
      description: pipeline.description,
      processor_sequence: pipeline.processor_sequence
    })
    setEditModal({ isOpen: true, pipeline, mode: 'edit' })
  }

  const handleCreatePipeline = () => {
    setPipelineForm({
      name: '',
      description: '',
      processor_sequence: []
    })
    setEditModal({ isOpen: true, pipeline: null, mode: 'create' })
  }

  const handleSavePipeline = async () => {
    try {
      if (editModal.mode === 'create') {
        await axios.post('/api/backend/processors/pipelines', pipelineForm)
      } else if (editModal.pipeline) {
        await axios.put(`/api/backend/processors/pipelines/${editModal.pipeline.id}`, pipelineForm)
      }
      
      setEditModal({ isOpen: false, pipeline: null, mode: 'create' })
      await loadPipelines()
    } catch (err: any) {
      setError(`Failed to save pipeline: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleDeletePipeline = async (pipelineId: number) => {
    if (!confirm('Are you sure you want to delete this pipeline?')) return

    try {
      await axios.delete(`/api/backend/processors/pipelines/${pipelineId}`)
      await loadPipelines()
    } catch (err: any) {
      setError(`Failed to delete pipeline: ${err.response?.data?.detail || err.message}`)
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

  // Load recent files and pipelines on component mount
  useEffect(() => {
    if (isLoggedIn) {
      loadRecentFiles()
      loadPipelines()
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
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <File className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded':
      case 'document_loaded':
      case 'active':
      case 'completed':
        return 'text-green-800 bg-green-50 border-green-200'
      case 'already_uploaded':
        return 'text-yellow-800 bg-yellow-50 border-yellow-200'
      case 'document_not_found':
      case 'failed':
        return 'text-red-800 bg-red-50 border-red-200'
      case 'running':
        return 'text-blue-800 bg-blue-50 border-blue-200'
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
          <p className="text-gray-600">Upload documents and process them using AI-powered pipelines.</p>
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

        {/* Pipeline Management Section */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center">
              <GitBranch className="w-5 h-5 mr-2" />
              Processing Pipelines
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={loadPipelines}
                disabled={loadingPipelines}
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${loadingPipelines ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={handleCreatePipeline}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center"
              >
                <Plus className="w-4 h-4 mr-1" />
                Create Pipeline
              </button>
            </div>
          </div>

          {loadingPipelines ? (
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-600">Loading pipelines...</p>
            </div>
          ) : pipelines.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <GitBranch className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="mb-4">No pipelines created yet</p>
              <button
                onClick={handleCreatePipeline}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
              >
                Create Your First Pipeline
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {pipelines.map((pipeline) => (
                <div key={pipeline.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(pipeline.status)}`}>
                        {getStatusIcon(pipeline.status)}
                        <span className="ml-1">{pipeline.status}</span>
                      </div>
                      <h3 className="font-semibold text-lg">{pipeline.name}</h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleExecutePipeline(pipeline.id)}
                        disabled={selectedFiles.size === 0}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
                        title={selectedFiles.size === 0 ? 'Select files to process' : `Run on ${selectedFiles.size} selected files`}
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Run ({selectedFiles.size})
                      </button>
                      <button
                        onClick={() => handleEditPipeline(pipeline)}
                        className="text-blue-600 hover:text-blue-800 p-1"
                        title="Edit pipeline"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeletePipeline(pipeline.id)}
                        className="text-red-600 hover:text-red-800 p-1"
                        title="Delete pipeline"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-3">{pipeline.description}</p>

                  <div className="flex items-center space-x-6 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Settings className="w-4 h-4" />
                      <span>{pipeline.processor_sequence.length} processors</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Activity className="w-4 h-4" />
                      <span>{pipeline.execution_count} runs</span>
                    </div>
                    {pipeline.average_execution_time && (
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>{pipeline.average_execution_time.toFixed(1)}s avg</span>
                      </div>
                    )}
                    {pipeline.last_executed && (
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4" />
                        <span>Last: {new Date(pipeline.last_executed).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Files Section with Checkboxes */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <List className="w-5 h-5 mr-2" />
              Recent Files
              {selectedFiles.size > 0 && (
                <span className="ml-2 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                  {selectedFiles.size} selected
                </span>
              )}
            </h2>
            <div className="flex items-center space-x-2">
              {recentFiles.length > 0 && (
                <label className="flex items-center space-x-2 text-sm text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedFiles.size === recentFiles.length && recentFiles.length > 0}
                    onChange={(e) => handleSelectAllFiles(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Select All</span>
                </label>
              )}
              <button
                onClick={loadRecentFiles}
                disabled={loadingFiles}
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${loadingFiles ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
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
                    <input
                      type="checkbox"
                      checked={selectedFiles.has(file.file_hash)}
                      onChange={(e) => handleFileCheckboxChange(file.file_hash, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
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
              {recentFiles.length >= 10 && (
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

        {/* Pipeline Edit Modal */}
        {editModal.isOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                  {editModal.mode === 'create' ? 'Create Pipeline' : 'Edit Pipeline'}
                </h2>
                <button
                  onClick={() => setEditModal({ isOpen: false, pipeline: null, mode: 'create' })}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6 overflow-y-auto max-h-[70vh]">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Pipeline Name
                    </label>
                    <input
                      type="text"
                      value={pipelineForm.name}
                      onChange={(e) => setPipelineForm({ ...pipelineForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter pipeline name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={pipelineForm.description}
                      onChange={(e) => setPipelineForm({ ...pipelineForm, description: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                      rows={3}
                      placeholder="Describe what this pipeline does"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Processor Sequence
                    </label>
                    <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                      <p>Pipeline contains {pipelineForm.processor_sequence.length} processors</p>
                      <p className="mt-1 text-xs">Note: Processor sequence editing will be available in the full processor management interface.</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                <button
                  onClick={() => setEditModal({ isOpen: false, pipeline: null, mode: 'create' })}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSavePipeline}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  {editModal.mode === 'create' ? 'Create' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Information Section */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Upload className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold mb-2">1. Upload</h3>
              <p className="text-sm text-gray-600">Select and upload your documents. Files are stored securely.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <GitBranch className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold mb-2">2. Create Pipeline</h3>
              <p className="text-sm text-gray-600">Build processing pipelines with multiple processors.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold mb-2">3. Select Files</h3>
              <p className="text-sm text-gray-600">Choose which files to process with your pipeline.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Play className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold mb-2">4. Execute</h3>
              <p className="text-sm text-gray-600">Run your pipeline and get processed results.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 