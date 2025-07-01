'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'

// Types
interface Processor {
  id: number
  name: string
  description: string
  processor_type: 'builtin' | 'user_defined' | 'custom'
  status: 'active' | 'inactive' | 'error' | 'testing'
  processor_code: string
  input_types: string[]
  output_types: string[]
  processing_capabilities: string[]
  usage_count: number
  version: string
  is_template: boolean
  created_at: string
  updated_at: string
}

interface Pipeline {
  id: number
  name: string
  description: string
  status: 'active' | 'inactive' | 'running' | 'completed' | 'failed'
  processor_sequence: ProcessorStep[]
  execution_count: number
  version: string
  is_template: boolean
  created_at: string
  updated_at: string
}

interface ProcessorStep {
  processor_id: number
  config: Record<string, any>
  order: number
}

interface PipelineExecution {
  id: number
  pipeline_id: number
  file_hash: string
  execution_id: string
  status: 'running' | 'completed' | 'failed'
  started_at: string
  completed_at?: string
  execution_time?: number
  error_details?: string
}

const ProcessorPipelineManager: React.FC = () => {
  const [processors, setProcessors] = useState<Processor[]>([])
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [executions, setExecutions] = useState<PipelineExecution[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('processors')
  
  // Dialog states
  const [showProcessorDialog, setShowProcessorDialog] = useState(false)
  const [showPipelineDialog, setShowPipelineDialog] = useState(false)
  const [showExecutionDialog, setShowExecutionDialog] = useState(false)
  
  // Form states
  const [selectedProcessor, setSelectedProcessor] = useState<Processor | null>(null)
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [processorForm, setProcessorForm] = useState({
    name: '',
    description: '',
    processor_code: '',
    input_types: [] as string[],
    output_types: [] as string[],
    processing_capabilities: [] as string[]
  })
  const [pipelineForm, setPipelineForm] = useState({
    name: '',
    description: '',
    processor_sequence: [] as ProcessorStep[]
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load processors
      const processorsResponse = await axios.get('/api/processors')
      setProcessors(processorsResponse.data.processors || [])
      
      // Load pipelines
      const pipelinesResponse = await axios.get('/api/processors/pipelines')
      setPipelines(pipelinesResponse.data.pipelines || [])
      
      // Load executions
      const executionsResponse = await axios.get('/api/processors/executions')
      setExecutions(executionsResponse.data.executions || [])
    } catch (error) {
      console.error('Failed to load data:', error)
      // Use mock data for demonstration
      loadMockData()
    } finally {
      setLoading(false)
    }
  }

  const loadMockData = () => {
    // Mock data for demonstration
    setProcessors([
      {
        id: 1,
        name: 'Text Chunker',
        description: 'Splits text into smaller chunks for processing',
        processor_type: 'builtin',
        status: 'active',
        processor_code: '# Text chunking implementation\nclass TextChunkerProcessor(AsyncProcessor):\n    # Implementation here',
        input_types: ['text'],
        output_types: ['chunks'],
        processing_capabilities: ['text_processing', 'chunking'],
        usage_count: 15,
        version: '1.0.0',
        is_template: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: 2,
        name: 'Vector Generator',
        description: 'Generates vector embeddings from text',
        processor_type: 'user_defined',
        status: 'active',
        processor_code: '# Vector generation implementation\nclass VectorProcessor(AsyncProcessor):\n    # Implementation here',
        input_types: ['chunks'],
        output_types: ['vectors'],
        processing_capabilities: ['embedding', 'vectorization'],
        usage_count: 8,
        version: '1.1.0',
        is_template: false,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z'
      }
    ])

    setPipelines([
      {
        id: 1,
        name: 'Document Processing Pipeline',
        description: 'Standard document processing with chunking and vectorization',
        status: 'active',
        processor_sequence: [
          { processor_id: 1, config: { chunk_size: 1000 }, order: 1 },
          { processor_id: 2, config: { vector_size: 128 }, order: 2 }
        ],
        execution_count: 25,
        version: '1.0.0',
        is_template: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-05T00:00:00Z'
      }
    ])

    setExecutions([
      {
        id: 1,
        pipeline_id: 1,
        file_hash: 'abc123def456',
        execution_id: 'exec-001',
        status: 'completed',
        started_at: '2024-01-10T10:00:00Z',
        completed_at: '2024-01-10T10:05:30Z',
        execution_time: 330
      },
      {
        id: 2,
        pipeline_id: 1,
        file_hash: 'def456ghi789',
        execution_id: 'exec-002',
        status: 'running',
        started_at: '2024-01-10T11:00:00Z'
      }
    ])
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      case 'error':
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'testing':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const handleCreateProcessor = async () => {
    try {
      await axios.post('/api/processors', processorForm)
      await loadData()
      setShowProcessorDialog(false)
      setProcessorForm({
        name: '',
        description: '',
        processor_code: '',
        input_types: [],
        output_types: [],
        processing_capabilities: []
      })
    } catch (error) {
      console.error('Failed to create processor:', error)
    }
  }

  const handleCreatePipeline = async () => {
    try {
      await axios.post('/api/processors/pipelines', pipelineForm)
      await loadData()
      setShowPipelineDialog(false)
      setPipelineForm({
        name: '',
        description: '',
        processor_sequence: []
      })
    } catch (error) {
      console.error('Failed to create pipeline:', error)
    }
  }

  const handleExecutePipeline = async (pipelineId: number, fileHash: string) => {
    try {
      const response = await axios.post(`/api/processors/pipelines/${pipelineId}/execute`, {
        file_hash: fileHash
      })
      console.log('Pipeline execution started:', response.data.execution_id)
      await loadData() // Refresh executions
    } catch (error) {
      console.error('Failed to execute pipeline:', error)
    }
  }

  const addProcessorToPipeline = (processorId: number) => {
    const newStep: ProcessorStep = {
      processor_id: processorId,
      config: {},
      order: pipelineForm.processor_sequence.length + 1
    }
    setPipelineForm({
      ...pipelineForm,
      processor_sequence: [...pipelineForm.processor_sequence, newStep]
    })
  }

  const removeProcessorFromPipeline = (index: number) => {
    const newSequence = pipelineForm.processor_sequence.filter((_, i) => i !== index)
    setPipelineForm({
      ...pipelineForm,
      processor_sequence: newSequence.map((step, i) => ({ ...step, order: i + 1 }))
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Processor & Pipeline Manager</h1>
          <p className="text-gray-600 mt-2">
            Create custom processors and build processing pipelines for your documents
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowProcessorDialog(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Processor
          </button>
          <button
            onClick={() => setShowPipelineDialog(true)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Pipeline
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['processors', 'pipelines', 'executions'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Processors Tab */}
      {activeTab === 'processors' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {processors.map(processor => (
            <div key={processor.id} className="border rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{processor.name}</h3>
                  <p className="text-gray-600 text-sm">{processor.description}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(processor.status)}`}>
                  {processor.status}
                </span>
              </div>
              
              <div className="flex gap-2 flex-wrap">
                {processor.processing_capabilities.map(cap => (
                  <span key={cap} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    {cap}
                  </span>
                ))}
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>Used {processor.usage_count} times</p>
                <p>Version: {processor.version}</p>
                <p>Type: {processor.processor_type}</p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setSelectedProcessor(processor)}
                  className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                >
                  View Code
                </button>
                <button className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pipelines Tab */}
      {activeTab === 'pipelines' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {pipelines.map(pipeline => (
            <div key={pipeline.id} className="border rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{pipeline.name}</h3>
                  <p className="text-gray-600 text-sm">{pipeline.description}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(pipeline.status)}`}>
                  {pipeline.status}
                </span>
              </div>
              
              <div>
                <p className="text-sm font-medium mb-2">Pipeline Steps:</p>
                <div className="space-y-1">
                  {pipeline.processor_sequence.map((step, index) => {
                    const processor = processors.find(p => p.id === step.processor_id)
                    return (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        <span className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs">
                          {step.order}
                        </span>
                        <span>{processor?.name}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>Executed {pipeline.execution_count} times</p>
                <p>Version: {pipeline.version}</p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowExecutionDialog(true)}
                  className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Execute
                </button>
                <button className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">
                  Configure
                </button>
                <button className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50">
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Executions Tab */}
      {activeTab === 'executions' && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-6 py-4">
            <h3 className="text-lg font-semibold">Pipeline Executions</h3>
            <p className="text-gray-600 text-sm">Track the status and results of pipeline executions</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Execution ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pipeline
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {executions.map(execution => {
                  const pipeline = pipelines.find(p => p.id === execution.pipeline_id)
                  return (
                    <tr key={execution.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                        {execution.execution_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {pipeline?.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                        {execution.file_hash.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(execution.status)}`}>
                          {execution.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {new Date(execution.started_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {execution.execution_time ? `${execution.execution_time}s` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button className="text-blue-600 hover:text-blue-900">
                          View Details
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Processor Creation Dialog */}
      {showProcessorDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Create Custom Processor</h2>
              <p className="text-gray-600 mb-6">Build a custom processor by writing AsyncProcessor code</p>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Processor Name
                    </label>
                    <input
                      type="text"
                      value={processorForm.name}
                      onChange={(e) => setProcessorForm({...processorForm, name: e.target.value})}
                      placeholder="e.g., Custom Text Analyzer"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <input
                      type="text"
                      value={processorForm.description}
                      onChange={(e) => setProcessorForm({...processorForm, description: e.target.value})}
                      placeholder="Brief description of what this processor does"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Processor Code
                  </label>
                  <textarea
                    value={processorForm.processor_code}
                    onChange={(e) => setProcessorForm({...processorForm, processor_code: e.target.value})}
                    placeholder="Write your AsyncProcessor class here..."
                    className="w-full h-80 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Your processor must inherit from AsyncProcessor and implement the process() method
                  </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <strong>Hint for after_process integration:</strong> The AsyncProcessor.after_process callback 
                    will automatically save processed data to appropriate storage systems (MinIO for files, 
                    vector databases for embeddings, graph databases for entities). Configure your processor's 
                    metadata to optimize storage routing.
                  </p>
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowProcessorDialog(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateProcessor}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Create Processor
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Creation Dialog */}
      {showPipelineDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Create Processing Pipeline</h2>
              <p className="text-gray-600 mb-6">Build a pipeline by selecting processors in sequence</p>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Pipeline Name
                    </label>
                    <input
                      type="text"
                      value={pipelineForm.name}
                      onChange={(e) => setPipelineForm({...pipelineForm, name: e.target.value})}
                      placeholder="e.g., Document Analysis Pipeline"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <input
                      type="text"
                      value={pipelineForm.description}
                      onChange={(e) => setPipelineForm({...pipelineForm, description: e.target.value})}
                      placeholder="Description of this pipeline"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Pipeline Steps
                  </label>
                  <div className="border rounded-lg p-4 space-y-3">
                    {pipelineForm.processor_sequence.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">
                        No processors added yet. Select processors from the list below.
                      </p>
                    ) : (
                      pipelineForm.processor_sequence.map((step, index) => {
                        const processor = processors.find(p => p.id === step.processor_id)
                        return (
                          <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center gap-3">
                              <span className="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs">
                                {index + 1}
                              </span>
                              <div>
                                <p className="font-medium">{processor?.name}</p>
                                <p className="text-sm text-gray-500">{processor?.description}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => removeProcessorFromPipeline(index)}
                              className="text-red-600 hover:text-red-800"
                            >
                              Remove
                            </button>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Available Processors
                  </label>
                  <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto border rounded-lg p-2">
                    {processors.filter(p => p.status === 'active').map(processor => (
                      <div
                        key={processor.id}
                        className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
                      >
                        <div>
                          <p className="font-medium text-sm">{processor.name}</p>
                          <p className="text-xs text-gray-500">{processor.description}</p>
                        </div>
                        <button
                          onClick={() => addProcessorToPipeline(processor.id)}
                          className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Add
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowPipelineDialog(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreatePipeline}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Create Pipeline
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Execution Dialog */}
      {showExecutionDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Execute Pipeline</h2>
              <p className="text-gray-600 mb-6">Select a file to process with this pipeline</p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    File Hash
                  </label>
                  <input
                    type="text"
                    placeholder="Enter file hash or select from uploaded files"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowExecutionDialog(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      // TODO: Implement execution
                      setShowExecutionDialog(false)
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Execute Pipeline
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Processor Code Viewer */}
      {selectedProcessor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">{selectedProcessor.name} - Code</h2>
              <p className="text-gray-600 mb-6">View and edit processor implementation</p>
              
              <textarea
                value={selectedProcessor.processor_code}
                readOnly
                className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md font-mono text-sm bg-gray-50"
              />
              
              <div className="flex justify-end mt-4">
                <button
                  onClick={() => setSelectedProcessor(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProcessorPipelineManager 