/**
 * WebhooksPage - Configure and manage webhooks
 */
import { useState } from 'react'
import { Webhook, Plus, Edit, Trash2, Power, PowerOff, Copy, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'

interface WebhookConfig {
  id: string
  name: string
  url: string
  events: string[]
  isActive: boolean
  secret: string
  createdAt: string
  lastTriggered?: string
  successCount: number
  failureCount: number
}

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([
    {
      id: '1',
      name: 'Document Created Notification',
      url: 'https://api.example.com/webhooks/document-created',
      events: ['document.created', 'document.updated'],
      isActive: true,
      secret: 'whsec_abc123def456ghi789',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
      lastTriggered: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      successCount: 1247,
      failureCount: 3
    },
    {
      id: '2',
      name: 'User Activity Logger',
      url: 'https://analytics.example.com/events',
      events: ['user.login', 'user.logout', 'search.performed'],
      isActive: true,
      secret: 'whsec_xyz789abc123def456',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
      lastTriggered: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      successCount: 3421,
      failureCount: 12
    },
    {
      id: '3',
      name: 'Backup Service Hook',
      url: 'https://backup.example.com/trigger',
      events: ['system.backup'],
      isActive: false,
      secret: 'whsec_backup789xyz123',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
      successCount: 45,
      failureCount: 0
    }
  ])

  const [showAddModal, setShowAddModal] = useState(false)
  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    events: [] as string[]
  })

  const availableEvents = [
    { id: 'document.created', label: 'Документ создан', category: 'Документы' },
    { id: 'document.updated', label: 'Документ обновлён', category: 'Документы' },
    { id: 'document.deleted', label: 'Документ удалён', category: 'Документы' },
    { id: 'user.login', label: 'Вход пользователя', category: 'Пользователи' },
    { id: 'user.logout', label: 'Выход пользователя', category: 'Пользователи' },
    { id: 'user.created', label: 'Пользователь создан', category: 'Пользователи' },
    { id: 'search.performed', label: 'Выполнен поиск', category: 'Поиск' },
    { id: 'system.backup', label: 'Резервное копирование', category: 'Система' },
    { id: 'system.error', label: 'Системная ошибка', category: 'Система' }
  ]

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

  const handleToggleActive = (id: string) => {
    setWebhooks(webhooks.map(w =>
      w.id === id ? { ...w, isActive: !w.isActive } : w
    ))
    const webhook = webhooks.find(w => w.id === id)
    toast.success(`Webhook "${webhook?.name}" ${webhook?.isActive ? 'деактивирован' : 'активирован'}`)
  }

  const handleDelete = (id: string) => {
    const webhook = webhooks.find(w => w.id === id)
    setWebhooks(webhooks.filter(w => w.id !== id))
    toast.success(`Webhook "${webhook?.name}" удалён`)
  }

  const handleCopySecret = (secret: string) => {
    navigator.clipboard.writeText(secret)
    toast.success('Секретный ключ скопирован')
  }

  const handleAddWebhook = () => {
    if (!newWebhook.name || !newWebhook.url || newWebhook.events.length === 0) {
      toast.error('Заполните все обязательные поля')
      return
    }

    const webhook: WebhookConfig = {
      id: Date.now().toString(),
      name: newWebhook.name,
      url: newWebhook.url,
      events: newWebhook.events,
      isActive: true,
      secret: `whsec_${Math.random().toString(36).substr(2, 20)}`,
      createdAt: new Date().toISOString(),
      successCount: 0,
      failureCount: 0
    }

    setWebhooks([...webhooks, webhook])
    setShowAddModal(false)
    setNewWebhook({ name: '', url: '', events: [] })
    toast.success('Webhook создан')
  }

  const toggleEvent = (eventId: string) => {
    if (newWebhook.events.includes(eventId)) {
      setNewWebhook({ ...newWebhook, events: newWebhook.events.filter(e => e !== eventId) })
    } else {
      setNewWebhook({ ...newWebhook, events: [...newWebhook.events, eventId] })
    }
  }

  const groupedEvents = availableEvents.reduce((acc, event) => {
    if (!acc[event.category]) acc[event.category] = []
    acc[event.category].push(event)
    return acc
  }, {} as Record<string, typeof availableEvents>)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Управление Webhooks</h1>
          <p className="text-gray-600 mt-1">Настройка вебхуков для интеграции с внешними сервисами</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Добавить Webhook
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Всего webhooks</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{webhooks.length}</div>
        </div>
        <div className="bg-white rounded-lg border border-green-200 p-4">
          <div className="text-sm text-gray-600">Активных</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {webhooks.filter(w => w.isActive).length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-blue-200 p-4">
          <div className="text-sm text-gray-600">Успешных вызовов</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {webhooks.reduce((sum, w) => sum + w.successCount, 0)}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-red-200 p-4">
          <div className="text-sm text-gray-600">Ошибок</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {webhooks.reduce((sum, w) => sum + w.failureCount, 0)}
          </div>
        </div>
      </div>

      {/* Webhooks List */}
      <div className="space-y-4">
        {webhooks.map((webhook) => (
          <div key={webhook.id} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex gap-4 flex-1">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Webhook className="w-6 h-6 text-primary-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">{webhook.name}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      webhook.isActive
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {webhook.isActive ? 'Активен' : 'Неактивен'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-3 font-mono break-all">{webhook.url}</div>

                  {/* Events */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {webhook.events.map((event) => (
                      <span key={event} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                        {event}
                      </span>
                    ))}
                  </div>

                  {/* Secret */}
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-600">Секретный ключ:</span>
                    <code className="px-2 py-1 bg-gray-100 rounded text-xs font-mono">{webhook.secret}</code>
                    <button
                      onClick={() => handleCopySecret(webhook.secret)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <Copy className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      {webhook.successCount} успешных
                    </span>
                    <span className="text-red-600">{webhook.failureCount} ошибок</span>
                    {webhook.lastTriggered && (
                      <span>Последний вызов: {formatTime(webhook.lastTriggered)}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggleActive(webhook.id)}
                  className={`p-2 rounded-lg transition-colors ${
                    webhook.isActive
                      ? 'text-green-600 hover:bg-green-50'
                      : 'text-gray-400 hover:bg-gray-50'
                  }`}
                  title={webhook.isActive ? 'Деактивировать' : 'Активировать'}
                >
                  {webhook.isActive ? <Power className="w-5 h-5" /> : <PowerOff className="w-5 h-5" />}
                </button>
                <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                  <Edit className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleDelete(webhook.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Webhook Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Добавить новый Webhook</h2>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Название</label>
                <input
                  type="text"
                  value={newWebhook.name}
                  onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Например: Document Created Notification"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">URL</label>
                <input
                  type="url"
                  value={newWebhook.url}
                  onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                  placeholder="https://api.example.com/webhooks/endpoint"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  События ({newWebhook.events.length} выбрано)
                </label>
                {Object.entries(groupedEvents).map(([category, events]) => (
                  <div key={category} className="mb-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">{category}</h4>
                    <div className="space-y-2">
                      {events.map((event) => (
                        <label key={event.id} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={newWebhook.events.includes(event.id)}
                            onChange={() => toggleEvent(event.id)}
                            className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                          />
                          <span className="text-sm text-gray-700">{event.label}</span>
                          <code className="text-xs text-gray-500 font-mono">({event.id})</code>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowAddModal(false)
                  setNewWebhook({ name: '', url: '', events: [] })
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Отмена
              </button>
              <button
                onClick={handleAddWebhook}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
