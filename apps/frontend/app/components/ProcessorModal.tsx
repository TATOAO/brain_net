'use client'

import React, { useState } from 'react'
import axios from 'axios'
import ProcessorSelector from './ProcessorSelector'

interface ProcessorStep {
  processor_id: string
  parameters: Record<string, any>
  stop_on_error?: boolean
}

interface ProcessorModalProps {
  isOpen: boolean
  onClose: () => void
  fileHash: string
  filename: string
  userId: number
  onProcessingComplete: (result: any) => void
}

export default function ProcessorModal({
  isOpen,
  onClose,
  fileHash,
  filename,
  userId,
  onProcessingComplete
}: ProcessorModalProps) {
  const [pipeline, setPipeline] = useState<ProcessorStep[]>([])
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleProcess = async () => {
    if (pipeline.length === 0) {
      setError('Please select at least one processor')
      return
    }

    setProcessing(true)
    setError(null)

    try {
      const response = await axios.post('/api/llm/processors/process', {
        file_hash: fileHash,
        user_id: userId,
        filename: filename,
        pipeline: pipeline
      })

      setResult(response.data)
      onProcessingComplete(response.data)
    } catch (err: any) {
      setError(`Processing failed: ${err.response?.data?.detail || err.message}`)
      console.error('Processing error:', err)
    } finally {
      setProcessing(false)
    }
  }

  const handleQuickChunk = async () => {
    setProcessing(true)
    setError(null)

    try {
      const response = await axios.post('/api/llm/processors/chunk', {
        file_hash: fileHash,
        user_id: userId,
        filename: filename,
        chunker_id: 'fixed_size_chunker',
        chunk_size: 1000,
        overlap: 200
      })

      setResult(response.data)
      onProcessingComplete(response.data)
    } catch (err: any) {
      setError(`Chunking failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setProcessing(false)
    }
  }

  const handleQuickNER = async () => {
    setProcessing(true)
    setError(null)

    try {
      const response = await axios.post('/api/llm/processors/extract-entities', {
        file_hash: fileHash,
        user_id: userId,
        filename: filename,
        ner_processor_id: 'simple_ner',
        entity_types: ['PERSON', 'EMAIL', 'PHONE', 'URL']
      })

      setResult(response.data)
      onProcessingComplete(response.data)
    } catch (err: any) {
      setError(`Entity extraction failed: ${err.response?.data?.detail || err.message}`)
      console.error('NER error:', err)
    } finally {
      setProcessing(false)
    }
  }

  const resetModal = () => {
    setPipeline([])
    setResult(null)
    setError(null)
    setProcessing(false)
  }

  const handleClose = () => {
    resetModal()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Process Document</h2>
            <p className="text-sm text-gray-600">{filename}</p>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {!result ? (
            <div className="space-y-6">
              {/* Quick Actions */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-sm mb-3">Quick Actions</h3>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={handleQuickChunk}
                    disabled={processing}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-300"
                  >
                    Quick Chunk (1000 chars)
                  </button>
                  <button
                    onClick={handleQuickNER}
                    disabled={processing}
                    className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-gray-300"
                  >
                    Extract Entities
                  </button>
                </div>
              </div>

              {/* Processor Selector */}
              <ProcessorSelector
                onPipelineChange={setPipeline}
                documentFormat="text/plain"
                initialPipeline={pipeline}
              />

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}
            </div>
          ) : (
            /* Results Display */
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-medium text-green-800 mb-2">Processing Complete!</h3>
                <p className="text-green-700 text-sm">
                  Status: {result.status}
                  {result.chunks_created && ` • ${result.chunks_created} chunks created`}
                  {result.entities_found && ` • ${result.entities_found} entities found`}
                </p>
              </div>

              {/* Show chunks if available */}
              {result.chunks && result.chunks.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-3">Document Chunks ({result.chunks.length})</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {result.chunks.slice(0, 5).map((chunk: any, index: number) => (
                      <div key={index} className="bg-gray-50 rounded p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-gray-600">
                            Chunk {chunk.metadata?.chunk_index + 1 || index + 1}
                          </span>
                          <span className="text-xs text-gray-500">
                            {chunk.content.length} chars
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-3">
                          {chunk.content.substring(0, 200)}
                          {chunk.content.length > 200 && '...'}
                        </p>
                      </div>
                    ))}
                    {result.chunks.length > 5 && (
                      <p className="text-sm text-gray-500 text-center">
                        ... and {result.chunks.length - 5} more chunks
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Show entities if available */}
              {result.entities && result.entities.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-3">Extracted Entities ({result.entities.length})</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {result.entities.slice(0, 10).map((entity: any, index: number) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 rounded p-2">
                        <div>
                          <span className="font-medium text-sm">{entity.text}</span>
                          <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {entity.type}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {Math.round(entity.confidence * 100)}% confidence
                        </span>
                      </div>
                    ))}
                    {result.entities.length > 10 && (
                      <p className="text-sm text-gray-500 text-center">
                        ... and {result.entities.length - 10} more entities
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Show processing results if available */}
              {result.processing_results && result.processing_results.length > 0 && (
                <div>
                  <h4 className="font-medium text-sm mb-3">Processing Steps</h4>
                  <div className="space-y-2">
                    {result.processing_results.map((stepResult: any, index: number) => (
                      <div key={index} className="bg-gray-50 rounded p-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{stepResult.processor_id}</span>
                          <span className={`px-2 py-1 text-xs rounded ${
                            stepResult.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : stepResult.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {stepResult.status}
                          </span>
                        </div>
                        {stepResult.processing_time && (
                          <p className="text-xs text-gray-500 mt-1">
                            Processing time: {stepResult.processing_time.toFixed(2)}s
                          </p>
                        )}
                        {stepResult.error_message && (
                          <p className="text-xs text-red-600 mt-1">{stepResult.error_message}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <div>
            {result && (
              <button
                onClick={resetModal}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Process Again
              </button>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded"
            >
              Close
            </button>
            {!result && (
              <button
                onClick={handleProcess}
                disabled={processing || pipeline.length === 0}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-300 min-w-[100px]"
              >
                {processing ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing...
                  </div>
                ) : (
                  'Process Document'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 