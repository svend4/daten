/**
 * Admin System Logs Page
 */
import { useEffect, useState } from 'react'
import { Server, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface LogEntry {
  timestamp: string
  level: string
  message: string
  source?: string
}

export default function AdminLogsPage() {
  const [loading, setLoading] = useState(true)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [limit, setLimit] = useState(100)

  useEffect(() => {
    fetchLogs()
  }, [limit])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const data = await api.getAdminLogs(limit)
      setLogs(data.logs || [])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load logs')
    } finally {
      setLoading(false)
    }
  }

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'bg-red-100 text-red-800'
      case 'warning': return 'bg-yellow-100 text-yellow-800'
      case 'info': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Server className="w-8 h-8 text-primary-600" />
            Системные логи
          </h1>
          <p className="text-gray-600 mt-1">Журнал событий и ошибок системы</p>
        </div>
        <div className="flex gap-2">
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value={50}>50 записей</option>
            <option value={100}>100 записей</option>
            <option value={500}>500 записей</option>
          </select>
          <button
            onClick={fetchLogs}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Обновить
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {logs.length > 0 ? (
          logs.map((log, idx) => (
            <div key={idx} className="p-4 hover:bg-gray-50 font-mono text-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${getLevelColor(log.level)}`}>
                      {log.level}
                    </span>
                    <span className="text-gray-500 text-xs">
                      {new Date(log.timestamp).toLocaleString('ru-RU')}
                    </span>
                    {log.source && (
                      <span className="text-gray-400 text-xs">
                        [{log.source}]
                      </span>
                    )}
                  </div>
                  <p className="text-gray-900">{log.message}</p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Логи не найдены</p>
          </div>
        )}
      </div>
    </div>
  )
}
