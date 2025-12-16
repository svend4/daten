/**
 * SessionManagementPage - View and manage active user sessions
 */
import { useState } from 'react'
import { Monitor, Smartphone, Tablet, MapPin, Clock, XCircle, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'

interface Session {
  id: string
  userId: string
  username: string
  device: string
  deviceType: 'desktop' | 'mobile' | 'tablet'
  browser: string
  ip: string
  location: string
  loginTime: string
  lastActive: string
  isCurrentSession: boolean
}

export default function SessionManagementPage() {
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: '1',
      userId: 'user-1',
      username: 'admin',
      device: 'Windows 11 PC',
      deviceType: 'desktop',
      browser: 'Chrome 120.0',
      ip: '192.168.1.100',
      location: 'Moscow, Russia',
      loginTime: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      lastActive: new Date().toISOString(),
      isCurrentSession: true
    },
    {
      id: '2',
      userId: 'user-1',
      username: 'admin',
      device: 'iPhone 15 Pro',
      deviceType: 'mobile',
      browser: 'Safari 17.0',
      ip: '192.168.1.105',
      location: 'Moscow, Russia',
      loginTime: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
      lastActive: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      isCurrentSession: false
    },
    {
      id: '3',
      userId: 'user-2',
      username: 'user123',
      device: 'MacBook Pro',
      deviceType: 'desktop',
      browser: 'Firefox 121.0',
      ip: '192.168.1.110',
      location: 'Saint Petersburg, Russia',
      loginTime: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
      lastActive: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      isCurrentSession: false
    },
    {
      id: '4',
      userId: 'user-3',
      username: 'user456',
      device: 'Samsung Galaxy Tab',
      deviceType: 'tablet',
      browser: 'Chrome 120.0',
      ip: '192.168.1.115',
      location: 'Novosibirsk, Russia',
      loginTime: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
      lastActive: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      isCurrentSession: false
    }
  ])

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType) {
      case 'mobile':
        return <Smartphone className="w-5 h-5" />
      case 'tablet':
        return <Tablet className="w-5 h-5" />
      default:
        return <Monitor className="w-5 h-5" />
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (minutes < 1) return 'Только что'
    if (minutes < 60) return `${minutes} мин назад`
    if (hours < 24) return `${hours} ч назад`
    return `${days} дн назад`
  }

  const formatDateTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleTerminateSession = (sessionId: string, isCurrentSession: boolean) => {
    if (isCurrentSession) {
      toast.error('Невозможно завершить текущую сессию')
      return
    }

    setSessions(sessions.filter(s => s.id !== sessionId))
    toast.success('Сессия успешно завершена')
  }

  const handleTerminateAllOthers = () => {
    setSessions(sessions.filter(s => s.isCurrentSession))
    toast.success('Все другие сессии завершены')
  }

  const activeSessions = sessions.length
  const currentUserSessions = sessions.filter(s => s.userId === 'user-1').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Управление сеансами</h1>
          <p className="text-gray-600 mt-1">Просмотр и управление активными сеансами пользователей</p>
        </div>
        <button
          onClick={handleTerminateAllOthers}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          <XCircle className="w-4 h-4" />
          Завершить другие сеансы
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Активных сеансов</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{activeSessions}</div>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Мои сеансы</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{currentUserSessions}</div>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Monitor className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Уникальных пользователей</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {new Set(sessions.map(s => s.userId)).size}
              </div>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Monitor className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      <div className="space-y-4">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`bg-white rounded-lg border p-6 ${
              session.isCurrentSession ? 'border-primary-300 ring-2 ring-primary-100' : 'border-gray-200'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex gap-4 flex-1">
                {/* Device Icon */}
                <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
                  {getDeviceIcon(session.deviceType)}
                </div>

                {/* Session Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">{session.device}</h3>
                    {session.isCurrentSession && (
                      <span className="px-2 py-1 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
                        Текущий сеанс
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Monitor className="w-4 h-4" />
                      <span>{session.browser}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <MapPin className="w-4 h-4" />
                      <span>{session.location}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>Вход: {formatDateTime(session.loginTime)}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>Активность: {formatTime(session.lastActive)}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-600 font-mono text-xs">
                      <span className="font-sans">IP:</span>
                      <span>{session.ip}</span>
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <span className="font-medium">Пользователь:</span>
                      <span>{session.username}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div>
                {!session.isCurrentSession && (
                  <button
                    onClick={() => handleTerminateSession(session.id, session.isCurrentSession)}
                    className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                    Завершить
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <CheckCircle className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Безопасность сеансов</p>
            <p>
              Рекомендуется завершать неиспользуемые сеансы и проверять подозрительные входы из неизвестных
              местоположений. Текущий сеанс невозможно завершить через эту страницу.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
