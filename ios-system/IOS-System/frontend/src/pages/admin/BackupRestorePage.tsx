/**
 * BackupRestorePage - System backup and restore functionality
 */
import { useState } from 'react'
import { Database, Download, Upload, Archive, Clock, HardDrive, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'

interface BackupRecord {
  id: string
  name: string
  createdAt: string
  size: number
  type: 'full' | 'incremental' | 'documents' | 'database'
  status: 'completed' | 'in_progress' | 'failed'
}

export default function BackupRestorePage() {
  const [backups] = useState<BackupRecord[]>([
    {
      id: '1',
      name: 'Full System Backup - 2025-01-15',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      size: 2458906112,
      type: 'full',
      status: 'completed'
    },
    {
      id: '2',
      name: 'Documents Backup - 2025-01-14',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
      size: 524288000,
      type: 'documents',
      status: 'completed'
    },
    {
      id: '3',
      name: 'Database Backup - 2025-01-13',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
      size: 104857600,
      type: 'database',
      status: 'completed'
    },
    {
      id: '4',
      name: 'Incremental Backup - 2025-01-12',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 96).toISOString(),
      size: 52428800,
      type: 'incremental',
      status: 'completed'
    }
  ])

  const [scheduleSettings] = useState({
    enabled: true,
    frequency: 'daily',
    time: '03:00',
    retention: 30,
    autoCleanup: true
  })

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getTypeColor = (type: string) => {
    const colors = {
      full: 'bg-blue-100 text-blue-800',
      incremental: 'bg-green-100 text-green-800',
      documents: 'bg-purple-100 text-purple-800',
      database: 'bg-yellow-100 text-yellow-800'
    }
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getTypeLabel = (type: string) => {
    const labels = {
      full: 'Полный',
      incremental: 'Инкрементальный',
      documents: 'Документы',
      database: 'База данных'
    }
    return labels[type as keyof typeof labels] || type
  }

  const handleCreateBackup = (type: string) => {
    toast.success(`Создание резервной копии (${getTypeLabel(type)}) запущено`)
  }

  const handleDownload = (backupId: string) => {
    const backup = backups.find(b => b.id === backupId)
    toast.success(`Скачивание резервной копии "${backup?.name}" начато`)
  }

  const handleRestore = (backupId: string) => {
    const backup = backups.find(b => b.id === backupId)
    toast.warning(`Восстановление из "${backup?.name}" запущено. Это может занять несколько минут.`)
  }

  const totalSize = backups.reduce((sum, b) => sum + b.size, 0)
  const completedCount = backups.filter(b => b.status === 'completed').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Резервное копирование</h1>
        <p className="text-gray-600 mt-1">Управление резервными копиями системы</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего копий</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{backups.length}</div>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Archive className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-green-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Завершённых</div>
              <div className="text-2xl font-bold text-green-600 mt-1">{completedCount}</div>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-purple-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Общий размер</div>
              <div className="text-2xl font-bold text-purple-600 mt-1">{formatSize(totalSize)}</div>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <HardDrive className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-blue-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Автобэкап</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">
                {scheduleSettings.enabled ? 'ВКЛ' : 'ВЫКЛ'}
              </div>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Create Backup */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Создать резервную копию</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => handleCreateBackup('full')}
            className="flex flex-col items-center p-4 border-2 border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <Database className="w-8 h-8 text-blue-600 mb-2" />
            <span className="font-medium text-gray-900">Полная копия</span>
            <span className="text-xs text-gray-600 mt-1">Вся система</span>
          </button>

          <button
            onClick={() => handleCreateBackup('incremental')}
            className="flex flex-col items-center p-4 border-2 border-green-200 rounded-lg hover:bg-green-50 transition-colors"
          >
            <Archive className="w-8 h-8 text-green-600 mb-2" />
            <span className="font-medium text-gray-900">Инкрементальная</span>
            <span className="text-xs text-gray-600 mt-1">Только изменения</span>
          </button>

          <button
            onClick={() => handleCreateBackup('documents')}
            className="flex flex-col items-center p-4 border-2 border-purple-200 rounded-lg hover:bg-purple-50 transition-colors"
          >
            <Download className="w-8 h-8 text-purple-600 mb-2" />
            <span className="font-medium text-gray-900">Документы</span>
            <span className="text-xs text-gray-600 mt-1">Только документы</span>
          </button>

          <button
            onClick={() => handleCreateBackup('database')}
            className="flex flex-col items-center p-4 border-2 border-yellow-200 rounded-lg hover:bg-yellow-50 transition-colors"
          >
            <Database className="w-8 h-8 text-yellow-600 mb-2" />
            <span className="font-medium text-gray-900">База данных</span>
            <span className="text-xs text-gray-600 mt-1">Только БД</span>
          </button>
        </div>
      </div>

      {/* Schedule Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Расписание автоматического создания</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="flex items-center gap-2 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={scheduleSettings.enabled}
                className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                readOnly
              />
              <span className="text-sm font-medium text-gray-700">Включить автоматическое резервное копирование</span>
            </label>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Частота</label>
                <select
                  value={scheduleSettings.frequency}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  disabled
                >
                  <option value="hourly">Каждый час</option>
                  <option value="daily">Ежедневно</option>
                  <option value="weekly">Еженедельно</option>
                  <option value="monthly">Ежемесячно</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Время</label>
                <input
                  type="time"
                  value={scheduleSettings.time}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  readOnly
                />
              </div>
            </div>
          </div>

          <div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Хранить копии (дней)
                </label>
                <input
                  type="number"
                  value={scheduleSettings.retention}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  min="1"
                  readOnly
                />
                <p className="text-xs text-gray-500 mt-1">Копии старше этого срока будут удалены</p>
              </div>

              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={scheduleSettings.autoCleanup}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    readOnly
                  />
                  <span className="text-sm text-gray-700">Автоматическая очистка старых копий</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Backup List */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">История резервных копий</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {backups.map((backup) => (
            <div key={backup.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex gap-4 flex-1">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Archive className="w-6 h-6 text-primary-600" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{backup.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getTypeColor(backup.type)}`}>
                        {getTypeLabel(backup.type)}
                      </span>
                      {backup.status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDate(backup.createdAt)}
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="w-4 h-4" />
                        {formatSize(backup.size)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownload(backup.id)}
                    className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                  >
                    <Download className="w-4 h-4" />
                    Скачать
                  </button>
                  <button
                    onClick={() => handleRestore(backup.id)}
                    className="flex items-center gap-2 px-4 py-2 text-green-600 hover:bg-green-50 rounded-lg"
                  >
                    <Upload className="w-4 h-4" />
                    Восстановить
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <Archive className="w-5 h-5 text-yellow-600" />
          </div>
          <div className="text-sm text-yellow-800">
            <p className="font-medium mb-1">Важная информация о резервном копировании</p>
            <p>
              Восстановление из резервной копии перезапишет текущие данные системы. Убедитесь, что вы
              выбрали правильную копию перед восстановлением. Рекомендуется хранить копии в надёжном месте.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
