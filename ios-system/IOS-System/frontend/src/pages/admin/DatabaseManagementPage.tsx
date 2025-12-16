/**
 * DatabaseManagementPage - Database management and optimization
 */
import { useState } from 'react'
import { Database, RefreshCw, Zap, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

export default function DatabaseManagementPage() {
  const [stats] = useState({
    totalSize: 2.4 * 1024 * 1024 * 1024,
    totalTables: 45,
    totalRecords: 1247893,
    indexSize: 512 * 1024 * 1024
  })

  const tables = [
    { name: 'documents', records: 847234, size: 1.2 * 1024 * 1024 * 1024 },
    { name: 'users', records: 1523, size: 2.5 * 1024 * 1024 },
    { name: 'search_index', records: 847234, size: 512 * 1024 * 1024 },
    { name: 'audit_logs', records: 398745, size: 256 * 1024 * 1024 }
  ]

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Управление базой данных</h1>
        <p className="text-gray-600 mt-1">Мониторинг и оптимизация базы данных</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Размер БД</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{formatSize(stats.totalSize)}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Таблиц</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.totalTables}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Записей</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.totalRecords.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Индексы</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{formatSize(stats.indexSize)}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Операции обслуживания</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button onClick={() => toast.success('Оптимизация запущена')} className="flex flex-col items-center p-4 border-2 border-blue-200 rounded-lg hover:bg-blue-50">
            <Zap className="w-8 h-8 text-blue-600 mb-2" />
            <span className="font-medium">Оптимизировать</span>
          </button>
          <button onClick={() => toast.success('Очистка запущена')} className="flex flex-col items-center p-4 border-2 border-green-200 rounded-lg hover:bg-green-50">
            <RefreshCw className="w-8 h-8 text-green-600 mb-2" />
            <span className="font-medium">Очистить</span>
          </button>
          <button onClick={() => toast.success('Переиндексация запущена')} className="flex flex-col items-center p-4 border-2 border-purple-200 rounded-lg hover:bg-purple-50">
            <Database className="w-8 h-8 text-purple-600 mb-2" />
            <span className="font-medium">Переиндексировать</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Таблицы</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Таблица</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Записей</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Размер</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {tables.map(table => (
                <tr key={table.name}>
                  <td className="px-6 py-4 font-mono text-sm">{table.name}</td>
                  <td className="px-6 py-4 text-sm">{table.records.toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm">{formatSize(table.size)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Рекомендации по обслуживанию</p>
            <p>Регулярная оптимизация помогает поддерживать производительность БД. Рекомендуется выполнять раз в неделю.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
