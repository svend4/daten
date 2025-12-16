/**
 * ApiLogsPage - View API request logs and monitoring
 */
import { useState } from 'react'
import { Activity, Filter, Download, CheckCircle, XCircle, Clock } from 'lucide-react'

interface ApiLog {
  id: string
  timestamp: string
  method: string
  endpoint: string
  statusCode: number
  responseTime: number
  ip: string
  userAgent: string
  tokenId?: string
  error?: string
}

export default function ApiLogsPage() {
  const [logs] = useState<ApiLog[]>([
    {
      id: '1',
      timestamp: new Date(Date.now() - 1000 * 30).toISOString(),
      method: 'GET',
      endpoint: '/api/documents',
      statusCode: 200,
      responseTime: 45,
      ip: '192.168.1.100',
      userAgent: 'ios-client/1.0.0',
      tokenId: 'token-abc123'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 1000 * 60).toISOString(),
      method: 'POST',
      endpoint: '/api/search',
      statusCode: 200,
      responseTime: 123,
      ip: '192.168.1.105',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0)',
      tokenId: 'token-xyz789'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 1000 * 90).toISOString(),
      method: 'POST',
      endpoint: '/api/documents',
      statusCode: 201,
      responseTime: 234,
      ip: '192.168.1.110',
      userAgent: 'ios-client/1.0.0',
      tokenId: 'token-abc123'
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 1000 * 120).toISOString(),
      method: 'GET',
      endpoint: '/api/ai/summarize',
      statusCode: 500,
      responseTime: 5432,
      ip: '192.168.1.115',
      userAgent: 'PostmanRuntime/7.32.3',
      tokenId: 'token-def456',
      error: 'Internal Server Error: AI service timeout'
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 1000 * 180).toISOString(),
      method: 'DELETE',
      endpoint: '/api/documents/123',
      statusCode: 404,
      responseTime: 12,
      ip: '203.0.113.42',
      userAgent: 'curl/7.68.0',
      error: 'Document not found'
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 1000 * 240).toISOString(),
      method: 'GET',
      endpoint: '/api/search',
      statusCode: 429,
      responseTime: 3,
      ip: '203.0.113.50',
      userAgent: 'python-requests/2.28.0',
      error: 'Rate limit exceeded'
    }
  ])

  const [filters, setFilters] = useState({
    method: '',
    status: '',
    endpoint: ''
  })

  const getMethodColor = (method: string) => {
    const colors = {
      GET: 'bg-blue-100 text-blue-800',
      POST: 'bg-green-100 text-green-800',
      PUT: 'bg-yellow-100 text-yellow-800',
      DELETE: 'bg-red-100 text-red-800',
      PATCH: 'bg-purple-100 text-purple-800'
    }
    return colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) return 'text-green-600'
    if (statusCode >= 400 && statusCode < 500) return 'text-yellow-600'
    if (statusCode >= 500) return 'text-red-600'
    return 'text-gray-600'
  }

  const getStatusIcon = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) return <CheckCircle className="w-4 h-4 text-green-600" />
    if (statusCode >= 400) return <XCircle className="w-4 h-4 text-red-600" />
    return <Clock className="w-4 h-4 text-gray-600" />
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const successCount = logs.filter(l => l.statusCode >= 200 && l.statusCode < 300).length
  const errorCount = logs.filter(l => l.statusCode >= 400).length
  const avgResponseTime = Math.round(logs.reduce((sum, l) => sum + l.responseTime, 0) / logs.length)

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'Method', 'Endpoint', 'Status', 'Response Time', 'IP', 'User Agent', 'Token'].join(','),
      ...logs.map(log =>
        [
          log.timestamp,
          log.method,
          log.endpoint,
          log.statusCode,
          log.responseTime,
          log.ip,
          log.userAgent,
          log.tokenId || ''
        ].join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `api_logs_${Date.now()}.csv`
    a.click()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Логи API</h1>
          <p className="text-gray-600 mt-1">Мониторинг и анализ запросов к API</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Download className="w-4 h-4" />
          Экспорт
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего запросов</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{logs.length}</div>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-green-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Успешных</div>
              <div className="text-2xl font-bold text-green-600 mt-1">{successCount}</div>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-red-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Ошибок</div>
              <div className="text-2xl font-bold text-red-600 mt-1">{errorCount}</div>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-purple-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Ср. время</div>
              <div className="text-2xl font-bold text-purple-600 mt-1">{avgResponseTime}ms</div>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <h2 className="font-semibold text-gray-900">Фильтры</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">HTTP метод</label>
            <select
              value={filters.method}
              onChange={(e) => setFilters({ ...filters, method: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все методы</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Статус</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все статусы</option>
              <option value="2xx">2xx (Успех)</option>
              <option value="4xx">4xx (Клиентские ошибки)</option>
              <option value="5xx">5xx (Серверные ошибки)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Эндпоинт</label>
            <input
              type="text"
              value={filters.endpoint}
              onChange={(e) => setFilters({ ...filters, endpoint: e.target.value })}
              placeholder="Поиск по эндпоинту..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Время</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Метод</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Эндпоинт</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Время</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {formatTime(log.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getMethodColor(log.method)}`}>
                      {log.method}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 font-mono">{log.endpoint}</div>
                    {log.error && (
                      <div className="text-xs text-red-600 mt-0.5">{log.error}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(log.statusCode)}
                      <span className={`text-sm font-medium ${getStatusColor(log.statusCode)}`}>
                        {log.statusCode}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm ${log.responseTime > 1000 ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                      {formatResponseTime(log.responseTime)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 font-mono">{log.ip}</div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">{log.userAgent}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Response Time Chart Placeholder */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Время ответа</h2>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="text-center text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-2" />
            <p>График времени ответа API</p>
            <p className="text-sm mt-1">(интеграция с графиками)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
