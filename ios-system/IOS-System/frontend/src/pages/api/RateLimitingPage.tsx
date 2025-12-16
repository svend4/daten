/**
 * RateLimitingPage - Configure API rate limiting rules
 */
import { useState } from 'react'
import { Gauge, Save, RefreshCw, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'

interface RateLimitRule {
  endpoint: string
  limit: number
  window: number
  enabled: boolean
}

export default function RateLimitingPage() {
  const [rules, setRules] = useState<RateLimitRule[]>([
    { endpoint: '/api/search', limit: 100, window: 60, enabled: true },
    { endpoint: '/api/documents', limit: 1000, window: 3600, enabled: true },
    { endpoint: '/api/ai/*', limit: 50, window: 60, enabled: true },
    { endpoint: '/api/export', limit: 10, window: 60, enabled: true },
    { endpoint: '/api/admin/*', limit: 200, window: 60, enabled: true }
  ])

  const [globalSettings, setGlobalSettings] = useState({
    defaultLimit: 1000,
    defaultWindow: 3600,
    enableByDefault: true,
    blockDuration: 300,
    whitelistIPs: '127.0.0.1, 10.0.0.0/8'
  })

  const handleUpdateRule = (endpoint: string, field: keyof RateLimitRule, value: number | boolean) => {
    setRules(rules.map(rule =>
      rule.endpoint === endpoint ? { ...rule, [field]: value } : rule
    ))
  }

  const handleSave = () => {
    toast.success('Настройки rate limiting сохранены')
  }

  const handleReset = () => {
    toast.info('Счётчики rate limiting сброшены')
  }

  const formatWindow = (seconds: number) => {
    if (seconds < 60) return `${seconds} сек`
    if (seconds < 3600) return `${seconds / 60} мин`
    return `${seconds / 3600} ч`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Rate Limiting</h1>
          <p className="text-gray-600 mt-1">Настройка ограничений частоты запросов к API</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            Сбросить счётчики
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Save className="w-4 h-4" />
            Сохранить
          </button>
        </div>
      </div>

      {/* Global Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Глобальные настройки</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Лимит по умолчанию (запросов)
            </label>
            <input
              type="number"
              value={globalSettings.defaultLimit}
              onChange={(e) => setGlobalSettings({ ...globalSettings, defaultLimit: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              min="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Временное окно (секунд)
            </label>
            <input
              type="number"
              value={globalSettings.defaultWindow}
              onChange={(e) => setGlobalSettings({ ...globalSettings, defaultWindow: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              min="1"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Длительность блокировки (секунд)
            </label>
            <input
              type="number"
              value={globalSettings.blockDuration}
              onChange={(e) => setGlobalSettings({ ...globalSettings, blockDuration: parseInt(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              min="0"
            />
            <p className="text-xs text-gray-500 mt-1">Время блокировки после превышения лимита</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Белый список IP адресов
            </label>
            <input
              type="text"
              value={globalSettings.whitelistIPs}
              onChange={(e) => setGlobalSettings({ ...globalSettings, whitelistIPs: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
              placeholder="127.0.0.1, 10.0.0.0/8"
            />
            <p className="text-xs text-gray-500 mt-1">IP адреса через запятую</p>
          </div>
        </div>

        <div className="mt-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={globalSettings.enableByDefault}
              onChange={(e) => setGlobalSettings({ ...globalSettings, enableByDefault: e.target.checked })}
              className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Включить rate limiting для новых эндпоинтов по умолчанию</span>
          </label>
        </div>
      </div>

      {/* Endpoint Rules */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Правила для эндпоинтов</h2>
          <p className="text-sm text-gray-600 mt-1">
            Настройка лимитов для конкретных API эндпоинтов
          </p>
        </div>

        <div className="divide-y divide-gray-200">
          {rules.map((rule) => (
            <div key={rule.endpoint} className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Gauge className="w-6 h-6 text-primary-600" />
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-900 font-mono">{rule.endpoint}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {rule.limit} запросов за {formatWindow(rule.window)}
                      </p>
                    </div>

                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={rule.enabled}
                        onChange={(e) => handleUpdateRule(rule.endpoint, 'enabled', e.target.checked)}
                        className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {rule.enabled ? 'Включено' : 'Выключено'}
                      </span>
                    </label>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Лимит запросов
                      </label>
                      <input
                        type="number"
                        value={rule.limit}
                        onChange={(e) => handleUpdateRule(rule.endpoint, 'limit', parseInt(e.target.value) || 0)}
                        disabled={!rule.enabled}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                        min="1"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Временное окно (секунд)
                      </label>
                      <input
                        type="number"
                        value={rule.window}
                        onChange={(e) => handleUpdateRule(rule.endpoint, 'window', parseInt(e.target.value) || 1)}
                        disabled={!rule.enabled}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                        min="1"
                      />
                    </div>
                  </div>

                  {/* Visual Indicator */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                      <span>Использовано: 0 / {rule.limit}</span>
                      <span>0%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-600 h-2 rounded-full" style={{ width: '0%' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Активных правил</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {rules.filter(r => r.enabled).length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-blue-200 p-4">
          <div className="text-sm text-gray-600">Запросов сегодня</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">45,234</div>
        </div>
        <div className="bg-white rounded-lg border border-red-200 p-4">
          <div className="text-sm text-gray-600">Заблокировано сегодня</div>
          <div className="text-2xl font-bold text-red-600 mt-1">127</div>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Как работает Rate Limiting</p>
            <p>
              Rate limiting ограничивает количество запросов от одного IP адреса или токена за определённый
              период времени. При превышении лимита клиент получит HTTP 429 (Too Many Requests) и будет
              временно заблокирован на указанное время.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
