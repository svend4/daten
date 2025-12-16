/**
 * HealthMonitoringPage - System health monitoring dashboard
 */
import { useState } from 'react'
import { Activity, Cpu, HardDrive, Wifi, AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react'

interface SystemMetric {
  name: string
  value: number
  unit: string
  status: 'healthy' | 'warning' | 'critical'
  threshold: number
}

interface ServiceStatus {
  name: string
  status: 'running' | 'stopped' | 'error'
  uptime: string
  lastCheck: string
  responseTime: number
}

export default function HealthMonitoringPage() {
  const [metrics] = useState<SystemMetric[]>([
    { name: 'CPU Usage', value: 45, unit: '%', status: 'healthy', threshold: 80 },
    { name: 'Memory Usage', value: 62, unit: '%', status: 'healthy', threshold: 85 },
    { name: 'Disk Usage', value: 73, unit: '%', status: 'warning', threshold: 90 },
    { name: 'Network Load', value: 28, unit: 'Mbps', status: 'healthy', threshold: 100 }
  ])

  const [services] = useState<ServiceStatus[]>([
    {
      name: 'API Server',
      status: 'running',
      uptime: '15d 7h 23m',
      lastCheck: new Date().toISOString(),
      responseTime: 45
    },
    {
      name: 'Database',
      status: 'running',
      uptime: '15d 7h 23m',
      lastCheck: new Date().toISOString(),
      responseTime: 12
    },
    {
      name: 'Redis Cache',
      status: 'running',
      uptime: '15d 7h 23m',
      lastCheck: new Date().toISOString(),
      responseTime: 3
    },
    {
      name: 'Search Engine',
      status: 'running',
      uptime: '15d 7h 23m',
      lastCheck: new Date().toISOString(),
      responseTime: 89
    },
    {
      name: 'Background Workers',
      status: 'running',
      uptime: '15d 7h 23m',
      lastCheck: new Date().toISOString(),
      responseTime: 0
    }
  ])

  const getMetricColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600'
      case 'warning':
        return 'text-yellow-600'
      case 'critical':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getMetricIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />
      default:
        return null
    }
  }

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800'
      case 'stopped':
        return 'bg-gray-100 text-gray-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const healthyServices = services.filter(s => s.status === 'running').length
  const warningMetrics = metrics.filter(m => m.status === 'warning').length
  const criticalMetrics = metrics.filter(m => m.status === 'critical').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Мониторинг системы</h1>
        <p className="text-gray-600 mt-1">Статус и производительность системных компонентов</p>
      </div>

      {/* Overall Status */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle className="w-8 h-8" />
              <h2 className="text-2xl font-bold">Система работает нормально</h2>
            </div>
            <p className="text-green-100">Все основные компоненты функционируют штатно</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{healthyServices}/{services.length}</div>
            <div className="text-green-100">Сервисов активно</div>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <div key={metric.name} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-sm text-gray-600">{metric.name}</div>
                <div className={`text-2xl font-bold mt-1 ${getMetricColor(metric.status)}`}>
                  {metric.value}{metric.unit}
                </div>
              </div>
              {getMetricIcon(metric.status)}
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full ${
                  metric.status === 'healthy' ? 'bg-green-600' :
                  metric.status === 'warning' ? 'bg-yellow-600' : 'bg-red-600'
                }`}
                style={{ width: `${Math.min((metric.value / metric.threshold) * 100, 100)}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>Норма: &lt; {metric.threshold}{metric.unit}</span>
              <span>{metric.status === 'healthy' ? 'OK' : metric.status === 'warning' ? 'Внимание' : 'Критично'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Services Status */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Статус сервисов</h2>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>Обновлено только что</span>
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {services.map((service) => (
            <div key={service.name} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Activity className="w-6 h-6 text-primary-600" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{service.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getServiceStatusColor(service.status)}`}>
                        {service.status === 'running' ? 'Работает' : service.status === 'stopped' ? 'Остановлен' : 'Ошибка'}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        Время работы: {service.uptime}
                      </span>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4" />
                        Отклик: {service.responseTime}ms
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg">
                    Перезапустить
                  </button>
                  <button className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg">
                    Подробнее
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <Cpu className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Процессор</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Модель:</span>
              <span className="text-gray-900">Intel Xeon E5-2680</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Ядра:</span>
              <span className="text-gray-900">8 физических, 16 потоков</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Частота:</span>
              <span className="text-gray-900">2.7 GHz</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <HardDrive className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Хранилище</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Всего:</span>
              <span className="text-gray-900">500 GB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Используется:</span>
              <span className="text-gray-900">365 GB (73%)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Доступно:</span>
              <span className="text-gray-900">135 GB</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <Wifi className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Сеть</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Входящий:</span>
              <span className="text-gray-900">18.5 Mbps</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Исходящий:</span>
              <span className="text-gray-900">9.7 Mbps</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Пинг:</span>
              <span className="text-gray-900">12 ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {(warningMetrics > 0 || criticalMetrics > 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex gap-3">
            <div className="flex-shrink-0">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="text-sm text-yellow-800">
              <p className="font-medium mb-1">Обнаружены проблемы с производительностью</p>
              <p>
                {warningMetrics > 0 && `${warningMetrics} метрик требуют внимания. `}
                {criticalMetrics > 0 && `${criticalMetrics} метрик в критическом состоянии. `}
                Рекомендуется проверить использование ресурсов.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
