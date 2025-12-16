/**
 * ApiTokensPage - Manage API access tokens
 */
import { useState } from 'react'
import { Key, Plus, Copy, Trash2, Eye, EyeOff, Calendar, Activity } from 'lucide-react'
import { toast } from 'sonner'

interface ApiToken {
  id: string
  name: string
  token: string
  permissions: string[]
  createdAt: string
  lastUsed?: string
  expiresAt?: string
  requestCount: number
  isActive: boolean
}

export default function ApiTokensPage() {
  const [tokens, setTokens] = useState<ApiToken[]>([
    {
      id: '1',
      name: 'Production App Token',
      token: 'ios_live_abc123def456ghi789jkl012mno345pqr678',
      permissions: ['read:documents', 'write:documents', 'read:search'],
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
      lastUsed: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      requestCount: 45287,
      isActive: true
    },
    {
      id: '2',
      name: 'Development Token',
      token: 'ios_test_xyz789abc123def456ghi789jkl012mno345',
      permissions: ['read:documents', 'read:search'],
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
      lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
      expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 15).toISOString(),
      requestCount: 1523,
      isActive: true
    },
    {
      id: '3',
      name: 'Analytics Integration',
      token: 'ios_live_pqr678stu901vwx234yza567bcd890efg123',
      permissions: ['read:analytics', 'read:logs'],
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
      lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      requestCount: 12453,
      isActive: true
    },
    {
      id: '4',
      name: 'Old Backend Token',
      token: 'ios_live_old123expired456token789',
      permissions: ['read:documents', 'write:documents', 'delete:documents'],
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 180).toISOString(),
      lastUsed: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
      requestCount: 98234,
      isActive: false
    }
  ])

  const [visibleTokens, setVisibleTokens] = useState<Set<string>>(new Set())
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newToken, setNewToken] = useState({
    name: '',
    permissions: [] as string[],
    expiresInDays: 0
  })

  const allPermissions = [
    { id: 'read:documents', label: 'Чтение документов', category: 'Документы' },
    { id: 'write:documents', label: 'Запись документов', category: 'Документы' },
    { id: 'delete:documents', label: 'Удаление документов', category: 'Документы' },
    { id: 'read:search', label: 'Поиск', category: 'Поиск' },
    { id: 'read:analytics', label: 'Чтение аналитики', category: 'Аналитика' },
    { id: 'read:logs', label: 'Чтение логов', category: 'Администрирование' },
    { id: 'write:settings', label: 'Изменение настроек', category: 'Администрирование' }
  ]

  const maskToken = (token: string) => {
    if (token.length < 20) return token
    return `${token.substring(0, 12)}${'•'.repeat(token.length - 24)}${token.substring(token.length - 12)}`
  }

  const toggleTokenVisibility = (id: string) => {
    const newVisible = new Set(visibleTokens)
    if (newVisible.has(id)) {
      newVisible.delete(id)
    } else {
      newVisible.add(id)
    }
    setVisibleTokens(newVisible)
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

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const handleCopyToken = (token: string) => {
    navigator.clipboard.writeText(token)
    toast.success('Токен скопирован в буфер обмена')
  }

  const handleDeleteToken = (id: string) => {
    const token = tokens.find(t => t.id === id)
    setTokens(tokens.filter(t => t.id !== id))
    toast.success(`Токен "${token?.name}" удалён`)
  }

  const handleCreateToken = () => {
    if (!newToken.name || newToken.permissions.length === 0) {
      toast.error('Заполните название и выберите хотя бы одно разрешение')
      return
    }

    const generatedToken = `ios_live_${Math.random().toString(36).substr(2, 36)}`
    const token: ApiToken = {
      id: Date.now().toString(),
      name: newToken.name,
      token: generatedToken,
      permissions: newToken.permissions,
      createdAt: new Date().toISOString(),
      expiresAt: newToken.expiresInDays > 0
        ? new Date(Date.now() + newToken.expiresInDays * 24 * 60 * 60 * 1000).toISOString()
        : undefined,
      requestCount: 0,
      isActive: true
    }

    setTokens([token, ...tokens])
    setShowCreateModal(false)
    setNewToken({ name: '', permissions: [], expiresInDays: 0 })

    // Auto-show the new token
    setVisibleTokens(new Set([token.id]))
    toast.success('Токен создан! Скопируйте его сейчас - больше вы его не увидите.')
  }

  const togglePermission = (permId: string) => {
    if (newToken.permissions.includes(permId)) {
      setNewToken({ ...newToken, permissions: newToken.permissions.filter(p => p !== permId) })
    } else {
      setNewToken({ ...newToken, permissions: [...newToken.permissions, permId] })
    }
  }

  const groupedPermissions = allPermissions.reduce((acc, perm) => {
    if (!acc[perm.category]) acc[perm.category] = []
    acc[perm.category].push(perm)
    return acc
  }, {} as Record<string, typeof allPermissions>)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Токены</h1>
          <p className="text-gray-600 mt-1">Управление токенами доступа к API системы</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Создать токен
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Всего токенов</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{tokens.length}</div>
        </div>
        <div className="bg-white rounded-lg border border-green-200 p-4">
          <div className="text-sm text-gray-600">Активных</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {tokens.filter(t => t.isActive).length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-blue-200 p-4">
          <div className="text-sm text-gray-600">Всего запросов</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">
            {tokens.reduce((sum, t) => sum + t.requestCount, 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-purple-200 p-4">
          <div className="text-sm text-gray-600">Средняя активность</div>
          <div className="text-2xl font-bold text-purple-600 mt-1">
            {Math.round(tokens.reduce((sum, t) => sum + t.requestCount, 0) / tokens.length).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Tokens List */}
      <div className="space-y-4">
        {tokens.map((token) => (
          <div
            key={token.id}
            className={`bg-white rounded-lg border p-6 ${
              token.isActive ? 'border-gray-200' : 'border-gray-300 bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex gap-4 flex-1">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  token.isActive ? 'bg-primary-100' : 'bg-gray-200'
                }`}>
                  <Key className={`w-6 h-6 ${token.isActive ? 'text-primary-600' : 'text-gray-500'}`} />
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">{token.name}</h3>
                    {!token.isActive && (
                      <span className="px-2 py-1 text-xs font-medium bg-gray-200 text-gray-600 rounded-full">
                        Неактивен
                      </span>
                    )}
                    {token.expiresAt && (
                      <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Истекает {formatDate(token.expiresAt)}
                      </span>
                    )}
                  </div>

                  {/* Token */}
                  <div className="flex items-center gap-2 mb-3">
                    <code className="px-3 py-2 bg-gray-100 rounded text-sm font-mono flex-1 break-all">
                      {visibleTokens.has(token.id) ? token.token : maskToken(token.token)}
                    </code>
                    <button
                      onClick={() => toggleTokenVisibility(token.id)}
                      className="p-2 hover:bg-gray-100 rounded"
                      title={visibleTokens.has(token.id) ? 'Скрыть' : 'Показать'}
                    >
                      {visibleTokens.has(token.id) ? (
                        <EyeOff className="w-4 h-4 text-gray-600" />
                      ) : (
                        <Eye className="w-4 h-4 text-gray-600" />
                      )}
                    </button>
                    <button
                      onClick={() => handleCopyToken(token.token)}
                      className="p-2 hover:bg-gray-100 rounded"
                      title="Копировать"
                    >
                      <Copy className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>

                  {/* Permissions */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {token.permissions.map((perm) => (
                      <span key={perm} className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-mono">
                        {perm}
                      </span>
                    ))}
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Activity className="w-4 h-4" />
                      {token.requestCount.toLocaleString()} запросов
                    </span>
                    {token.lastUsed && (
                      <span>Последнее использование: {formatTime(token.lastUsed)}</span>
                    )}
                    <span>Создан: {formatDate(token.createdAt)}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDeleteToken(token.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                  title="Удалить токен"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Token Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Создать новый API токен</h2>
              <p className="text-sm text-gray-600 mt-1">
                Токен будет показан только один раз. Сохраните его в безопасном месте.
              </p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Название токена</label>
                <input
                  type="text"
                  value={newToken.name}
                  onChange={(e) => setNewToken({ ...newToken, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Например: Production App Token"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Срок действия (дней)
                </label>
                <input
                  type="number"
                  value={newToken.expiresInDays}
                  onChange={(e) => setNewToken({ ...newToken, expiresInDays: parseInt(e.target.value) || 0 })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="0 = без срока действия"
                  min="0"
                />
                <p className="text-xs text-gray-500 mt-1">0 = токен без срока действия</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Разрешения ({newToken.permissions.length} выбрано)
                </label>
                {Object.entries(groupedPermissions).map(([category, perms]) => (
                  <div key={category} className="mb-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">{category}</h4>
                    <div className="space-y-2">
                      {perms.map((perm) => (
                        <label key={perm.id} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={newToken.permissions.includes(perm.id)}
                            onChange={() => togglePermission(perm.id)}
                            className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                          />
                          <span className="text-sm text-gray-700">{perm.label}</span>
                          <code className="text-xs text-gray-500 font-mono">({perm.id})</code>
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
                  setShowCreateModal(false)
                  setNewToken({ name: '', permissions: [], expiresInDays: 0 })
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Отмена
              </button>
              <button
                onClick={handleCreateToken}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Создать токен
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <Key className="w-5 h-5 text-yellow-600" />
          </div>
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Безопасность токенов</p>
            <p>
              Храните токены в безопасном месте. Не передавайте их по незащищённым каналам и не
              публикуйте в публичных репозиториях. При компрометации немедленно удалите токен.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
