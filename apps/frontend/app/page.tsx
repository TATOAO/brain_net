'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  Activity, 
  Database, 
  Search, 
  Network, 
  HardDrive, 
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react'

interface HealthStatus {
  healthy: boolean
  timestamp: string
  details?: any
  response_time?: number
}

interface ServiceHealth {
  [key: string]: HealthStatus
}

interface DetailedHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  services: ServiceHealth
}

const serviceIcons = {
  postgres: Database,
  elasticsearch: Search,
  neo4j: Network,
  minio: HardDrive,
  redis: Zap,
}

const serviceNames = {
  postgres: 'PostgreSQL',
  elasticsearch: 'Elasticsearch',
  neo4j: 'Neo4j',
  minio: 'MinIO',
  redis: 'Redis',
}

export default function Home() {
  const [healthData, setHealthData] = useState<DetailedHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchHealthData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Always use the proxy route in development to avoid CORS issues
      const endpoint = '/api/backend/health/detailed'
      
      console.log('Fetching health data from:', endpoint)
      const response = await axios.get(endpoint)
      setHealthData(response.data)
      setLastUpdated(new Date())
    } catch (err) {
      setError('Failed to fetch health data')
      console.error('Error fetching health data:', err)
      console.error('Full error details:', {
        message: err.message,
        code: err.code,
        config: err.config
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealthData()
    // Refresh every 10 seconds
    const interval = setInterval(fetchHealthData, 10000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'unhealthy':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusIcon = (healthy: boolean) => {
    return healthy ? (
      <CheckCircle className="w-5 h-5 text-green-600" />
    ) : (
      <XCircle className="w-5 h-5 text-red-600" />
    )
  }

  const getOverallStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-8 h-8 text-green-600" />
      case 'degraded':
        return <AlertCircle className="w-8 h-8 text-yellow-600" />
      case 'unhealthy':
        return <XCircle className="w-8 h-8 text-red-600" />
      default:
        return <Activity className="w-8 h-8 text-gray-600" />
    }
  }

  if (loading && !healthData) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="flex items-center space-x-2">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span>Loading health data...</span>
        </div>
      </div>
    )
  }

  if (error && !healthData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-2">
          <XCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="text-lg font-semibold text-red-800">Error</h3>
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchHealthData}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      {healthData && (
        <div className={`border rounded-lg p-6 ${getStatusColor(healthData.status)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getOverallStatusIcon(healthData.status)}
              <div>
                <h2 className="text-2xl font-bold capitalize">
                  System {healthData.status}
                </h2>
                <p className="text-sm opacity-75">
                  Last updated: {lastUpdated?.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              onClick={fetchHealthData}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 bg-white bg-opacity-50 rounded-md hover:bg-opacity-75 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      )}

      {/* Individual Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {healthData?.services && Object.entries(healthData.services).map(([serviceName, status]) => {
          const IconComponent = serviceIcons[serviceName as keyof typeof serviceIcons] || Activity
          const displayName = serviceNames[serviceName as keyof typeof serviceNames] || serviceName

          return (
            <div
              key={serviceName}
              className={`border rounded-lg p-6 ${status.healthy 
                ? 'bg-white border-gray-200' 
                : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <IconComponent className="w-6 h-6 text-gray-600" />
                  <h3 className="text-lg font-semibold">{displayName}</h3>
                </div>
                {getStatusIcon(status.healthy)}
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${status.healthy ? 'text-green-600' : 'text-red-600'}`}>
                    {status.healthy ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
                
                {status.response_time && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Response Time:</span>
                    <span className="font-medium">{status.response_time}ms</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span className="text-gray-600">Last Check:</span>
                  <span className="font-medium">
                    {new Date(status.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                {status.details && Object.keys(status.details).length > 0 && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                      View Details
                    </summary>
                    <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
                      {JSON.stringify(status.details, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div className="text-center text-gray-500 text-sm">
        <p>Health checks are automatically refreshed every 10 seconds</p>
      </div>
    </div>
  )
} 