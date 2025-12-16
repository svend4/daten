/**
 * Admin Services Status Page
 */
import { useEffect, useState } from 'react'
import { Activity, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

interface Service {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  uptime: string
  last_check: string
}

export default function AdminServicesPage() {
  const [loading, setLoading] = useState(true)
  const [services, setServices] = useState<Service[]>([])

  useEffect(() => {
    fetchServices()
  }, [])

  const fetchServices = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/admin/services')
      setServices(response.data.services || [])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load services')
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
            <Activity className="w-8 h-8 text-primary-600" />
            Статус сервисов
          </h1>
          <p className="text-gray-600 mt-1">Мониторинг всех сервисов системы</p>
        </div>
        <button
          onClick={fetchServices}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Обновить
        </button>
      </div>

      {/* Services List */}
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {services.length > 0 ? (
          services.map((service, idx) => (
            <div key={idx} className="p-4 hover:bg-gray-50 transition">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {service.status === 'healthy' ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : (
                    <XCircle className="w-6 h-6 text-red-500" />
                  )}
                  <div>
                    <div className="font-semibold text-gray-900">{service.name}</div>
                    <div className="text-sm text-gray-500">Uptime: {service.uptime}</div>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  Last check: {service.last_check}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12 text-gray-600">
            Нет данных о сервисах
          </div>
        )}
      </div>
    </div>
  )
}
