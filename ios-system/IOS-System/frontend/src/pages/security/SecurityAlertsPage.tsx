/**
 * SecurityAlertsPage - View and manage security alerts and notifications
 */
import { useState } from 'react'
import { AlertTriangle, Shield, XCircle, CheckCircle, Bell, BellOff, Trash2, Eye } from 'lucide-react'
import { toast } from 'sonner'

interface SecurityAlert {
  id: string
  type: 'critical' | 'warning' | 'info'
  title: string
  description: string
  timestamp: string
  source: string
  isRead: boolean
  isResolved: boolean
}

export default function SecurityAlertsPage() {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([
    {
      id: '1',
      type: 'critical',
      title: 'Обнаружена подозрительная активность',
      description: 'Множественные неудачные попытки входа с IP адреса 203.0.113.42',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      source: 'Authentication System',
      isRead: false,
      isResolved: false
    },
    {
      id: '2',
      type: 'warning',
      title: 'Необычное время доступа',
      description: 'Пользователь user123 вошёл в систему в 3:00 AM',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      source: 'Access Monitor',
      isRead: false,
      isResolved: false
    },
    {
      id: '3',
      type: 'info',
      title: 'Обновление политики безопасности',
      description: 'Минимальная длина пароля увеличена до 12 символов',
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      source: 'Security Policy',
      isRead: true,
      isResolved: true
    },
    {
      id: '4',
      type: 'warning',
      title: 'Доступ из нового местоположения',
      description: 'Пользователь admin вошёл из Novosibirsk (обычно Moscow)',
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      source: 'Geo-Location Monitor',
      isRead: true,
      isResolved: false
    },
    {
      id: '5',
      type: 'critical',
      title: 'Попытка SQL инъекции заблокирована',
      description: 'Обнаружена и заблокирована попытка SQL инъекции в форме поиска',
      timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
      source: 'WAF System',
      isRead: true,
      isResolved: true
    }
  ])

  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info' | 'unread'>('all')

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <XCircle className="w-5 h-5 text-red-600" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      default:
        return <Shield className="w-5 h-5 text-blue-600" />
    }
  }

  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'critical':
        return 'border-red-200 bg-red-50'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50'
      default:
        return 'border-blue-200 bg-blue-50'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)

    if (minutes < 1) return 'Только что'
    if (minutes < 60) return `${minutes} мин назад`
    if (hours < 24) return `${hours} ч назад`

    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleMarkAsRead = (id: string) => {
    setAlerts(alerts.map(a => a.id === id ? { ...a, isRead: true } : a))
    toast.success('Оповещение отмечено как прочитанное')
  }

  const handleResolve = (id: string) => {
    setAlerts(alerts.map(a => a.id === id ? { ...a, isResolved: true, isRead: true } : a))
    toast.success('Оповещение отмечено как решённое')
  }

  const handleDelete = (id: string) => {
    setAlerts(alerts.filter(a => a.id !== id))
    toast.success('Оповещение удалено')
  }

  const handleMarkAllAsRead = () => {
    setAlerts(alerts.map(a => ({ ...a, isRead: true })))
    toast.success('Все оповещения отмечены как прочитанные')
  }

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true
    if (filter === 'unread') return !alert.isRead
    return alert.type === filter
  })

  const criticalCount = alerts.filter(a => a.type === 'critical' && !a.isResolved).length
  const warningCount = alerts.filter(a => a.type === 'warning' && !a.isResolved).length
  const unreadCount = alerts.filter(a => !a.isRead).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Оповещения безопасности</h1>
          <p className="text-gray-600 mt-1">Мониторинг и управление предупреждениями системы безопасности</p>
        </div>
        <button
          onClick={handleMarkAllAsRead}
          disabled={unreadCount === 0}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <CheckCircle className="w-4 h-4" />
          Отметить все прочитанными
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего оповещений</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{alerts.length}</div>
            </div>
            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
              <Bell className="w-6 h-6 text-gray-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-red-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Критические</div>
              <div className="text-2xl font-bold text-red-600 mt-1">{criticalCount}</div>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-yellow-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Предупреждения</div>
              <div className="text-2xl font-bold text-yellow-600 mt-1">{warningCount}</div>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-primary-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Непрочитанные</div>
              <div className="text-2xl font-bold text-primary-600 mt-1">{unreadCount}</div>
            </div>
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <BellOff className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'all'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Все ({alerts.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'unread'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Непрочитанные ({unreadCount})
        </button>
        <button
          onClick={() => setFilter('critical')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'critical'
              ? 'bg-red-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Критические ({criticalCount})
        </button>
        <button
          onClick={() => setFilter('warning')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'warning'
              ? 'bg-yellow-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Предупреждения ({warningCount})
        </button>
        <button
          onClick={() => setFilter('info')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            filter === 'info'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          Информационные
        </button>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <Bell className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Нет оповещений для отображения</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-lg border p-4 ${getAlertStyle(alert.type)} ${
                !alert.isRead ? 'ring-2 ring-primary-200' : ''
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="flex-shrink-0 mt-1">{getAlertIcon(alert.type)}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{alert.title}</h3>
                      <p className="text-sm text-gray-700">{alert.description}</p>
                    </div>
                    {!alert.isRead && (
                      <span className="flex-shrink-0 w-2 h-2 bg-primary-600 rounded-full mt-2"></span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-600 mb-3">
                    <span className="font-medium">{alert.source}</span>
                    <span>•</span>
                    <span>{formatTime(alert.timestamp)}</span>
                    {alert.isResolved && (
                      <>
                        <span>•</span>
                        <span className="text-green-600 font-medium">Решено</span>
                      </>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    {!alert.isRead && (
                      <button
                        onClick={() => handleMarkAsRead(alert.id)}
                        className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:bg-blue-100 rounded transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                        Прочитано
                      </button>
                    )}
                    {!alert.isResolved && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="flex items-center gap-1 px-3 py-1 text-sm text-green-600 hover:bg-green-100 rounded transition-colors"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Решить
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(alert.id)}
                      className="flex items-center gap-1 px-3 py-1 text-sm text-red-600 hover:bg-red-100 rounded transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
