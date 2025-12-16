/**
 * Admin Statistics Page
 */
import { useEffect, useState } from 'react'
import { BarChart3, Loader2, Users, FileText, Database, Activity } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

interface Stats {
  total_users: number
  total_documents: number
  total_searches: number
  active_sessions: number
  database_size: string
  cache_hit_rate: number
}

export default function AdminStatsPage() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/admin/stats')
      setStats(response.data)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load statistics')
    } finally {
      setLoading(false)
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
            <BarChart3 className="w-8 h-8 text-primary-600" />
            Статистика системы
          </h1>
          <p className="text-gray-600 mt-1">Общая статистика и метрики системы</p>
        </div>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Обновить
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <div className="text-sm text-gray-600">Пользователи</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.total_users || 0}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <div className="text-sm text-gray-600">Документы</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.total_documents || 0}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Activity className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <div className="text-sm text-gray-600">Активные сессии</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.active_sessions || 0}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Database className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <div className="text-sm text-gray-600">Размер БД</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.database_size || 'N/A'}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6 md:col-span-2">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <div className="text-sm text-gray-600">Cache Hit Rate</div>
              <div className="text-2xl font-bold text-gray-900">
                {stats?.cache_hit_rate ? `${(stats.cache_hit_rate * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
