'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface ProcessorInfo {
  processor_id: string
  name: string
  description: string
  version: string
  processing_type: string
  supported_formats: string[]
  required_parameters: Record<string, any>
  optional_parameters: Record<string, any>
  enabled: boolean
  dependencies: string[]
}

interface ProcessorStep {
  processor_id: string
  parameters: Record<string, any>
  stop_on_error?: boolean
}

interface ProcessorSelectorProps {
  onPipelineChange: (pipeline: ProcessorStep[]) => void
  documentFormat?: string
  initialPipeline?: ProcessorStep[]
}

export default function ProcessorSelector({ 
  onPipelineChange, 
  documentFormat = 'text/plain',
  initialPipeline = []
}: ProcessorSelectorProps) {
  const [processors, setProcessors] = useState<Record<string, ProcessorInfo[]>>({})
  const [pipeline, setPipeline] = useState<ProcessorStep[]>(initialPipeline)
  const [loading, setLoading] = useState(true)
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [selectedTab, setSelectedTab] = useState<string>('chunking')

  useEffect(() => {
    loadProcessors()
    loadSuggestions()
  }, [documentFormat])

  useEffect(() => {
    onPipelineChange(pipeline)
  }, [pipeline, onPipelineChange])

  const loadProcessors = async () => {
    try {
      const response = await axios.get('/api/llm/processors')
      setProcessors(response.data.processors_by_type)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load processors:', error)
      setLoading(false)
    }
  }

  const loadSuggestions = async () => {
    try {
      const response = await axios.post('/api/llm/processors/suggestions', {
        document_format: documentFormat
      })
      setSuggestions(response.data.suggestions)
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    }
  }

  const addProcessorStep = (processorId: string) => {
    const processor = findProcessor(processorId)
    if (!processor) return

    const defaultParams: Record<string, any> = {}
    
    // Set default values for optional parameters
    Object.entries(processor.optional_parameters).forEach(([key, paramInfo]: [string, any]) => {
      if (paramInfo.default !== undefined) {
        defaultParams[key] = paramInfo.default
      }
    })

    const newStep: ProcessorStep = {
      processor_id: processorId,
      parameters: defaultParams,
      stop_on_error: true
    }

    setPipeline([...pipeline, newStep])
  }

  const removeProcessorStep = (index: number) => {
    setPipeline(pipeline.filter((_, i) => i !== index))
  }

  const findProcessor = (processorId: string): ProcessorInfo | undefined => {
    for (const processorList of Object.values(processors)) {
      const processor = processorList.find(p => p.processor_id === processorId)
      if (processor) return processor
    }
    return undefined
  }

  const applySuggestion = (suggestion: any) => {
    setPipeline(suggestion.pipeline)
  }

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Suggested Configurations</h3>
          <div className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <div key={index} className="flex items-center justify-between bg-white rounded p-3">
                <div>
                  <h4 className="font-medium text-sm">{suggestion.name}</h4>
                  <p className="text-xs text-gray-600">{suggestion.description}</p>
                </div>
                <button
                  onClick={() => applySuggestion(suggestion)}
                  className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Apply
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processor Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {Object.keys(processors).map((processingType) => (
            <button
              key={processingType}
              onClick={() => setSelectedTab(processingType)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                selectedTab === processingType
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {processingType.replace('_', ' ').toUpperCase()}
              <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                {processors[processingType]?.length || 0}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Available Processors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {processors[selectedTab]?.map((processor) => (
          <div key={processor.processor_id} className="border rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-medium text-sm">{processor.name}</h3>
                <p className="text-xs text-gray-600 mt-1">{processor.description}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {processor.supported_formats.map((format) => (
                    <span key={format} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                      {format}
                    </span>
                  ))}
                </div>
              </div>
              <button
                onClick={() => addProcessorStep(processor.processor_id)}
                disabled={!processor.enabled}
                className="ml-3 px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300"
              >
                Add
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Processing Pipeline */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-sm mb-4">Processing Pipeline ({pipeline.length} steps)</h3>
        
        {pipeline.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">
            No processors selected. Add processors from the tabs above to build your pipeline.
          </p>
        ) : (
          <div className="space-y-3">
            {pipeline.map((step, index) => {
              const processor = findProcessor(step.processor_id)
              if (!processor) return null

              return (
                <div key={index} className="bg-white rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                        {index + 1}
                      </span>
                      <div>
                        <h4 className="font-medium text-sm">{processor.name}</h4>
                        <p className="text-xs text-gray-600">{processor.processing_type}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeProcessorStep(index)}
                      className="text-xs text-red-600 hover:text-red-800"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
} 