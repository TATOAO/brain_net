'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useAuth } from '@/app/contexts/AuthContext'
import Header from '@/app/components/Header'
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
  RefreshCw,
  Shield,
  Users,
  BarChart3
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
  const { user, isLoggedIn, loading: authLoading } = useAuth()
  const [healthData, setHealthData] = useState<DetailedHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [documentCount, setDocumentCount] = useState<number | null>(null)

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
    } catch (err: any) {
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

  const fetchDocumentCount = async () => {
    if (!isLoggedIn || !user) return
    
    try {
      console.log('Fetching document count for user:', user.username)
      const response = await axios.get('/api/backend/upload/my-files', {
        params: {
          limit: 1,  // We only need the count, not the actual files
          offset: 0
        }
      })
      console.log('Document count response:', response.data)
      setDocumentCount(response.data.total_count)
    } catch (err: any) {
      console.error('Error fetching document count:', err)
      setDocumentCount(0) // Set to 0 on error
    }
  }

  useEffect(() => {
    fetchHealthData()
    // Refresh every 10 seconds
    const interval = setInterval(fetchHealthData, 10000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (isLoggedIn && !authLoading) {
      fetchDocumentCount()
    }
  }, [isLoggedIn, authLoading])

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

  // Show welcome page for non-authenticated users
  if (!isLoggedIn && !authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header />
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-16">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Welcome to Brain Net
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              An intelligent and highly visualized RAG system for local knowledge base management. 
              Organize, search, and interact with your documents using advanced AI capabilities.
            </p>
            <div className="flex justify-center space-x-4">
              <a
                href="/signup"
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Get Started
              </a>
              <a
                href="/login"
                className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold border border-blue-600 hover:bg-blue-50 transition-colors"
              >
                Sign In
              </a>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Smart Knowledge Management</h3>
              <p className="text-gray-600">
                Upload and organize your documents with intelligent categorization and semantic search capabilities.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Advanced Search</h3>
              <p className="text-gray-600">
                Find information quickly with AI-powered search that understands context and intent.
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <BarChart3 className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Visual Analytics</h3>
              <p className="text-gray-600">
                Gain insights from your knowledge base with interactive visualizations and analytics.
              </p>
            </div>
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
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Brain Net Dashboard
          </h1>
          <p className="text-gray-600">
            {isLoggedIn ? `Welcome back, ${user?.username || user?.email}!` : 'Monitor the health status of all Brain Net backend services'}
          </p>
        </div>
        
        {isLoggedIn && (
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Documents</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {documentCount !== null ? documentCount : '--'}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Search className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Queries</p>
                  <p className="text-2xl font-bold text-gray-900">--</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Users className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900">1</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Shield className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">System Status</p>
                  <p className="text-2xl font-bold text-gray-900">Online</p>
                </div>
              </div>
            </div>
          </div>
        )}

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
      </div>
    </div>
  )
} 