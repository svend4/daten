/**
 * AuditTrailPage - View and filter system audit logs
 */
import { useState } from 'react'
import { Search, Filter, Download, Calendar, User, FileText, AlertCircle } from 'lucide-react'

interface AuditLog {
  id: string
  timestamp: string
  user: string
  action: string
  resource: string
  details: string
  ip: string
  status: 'success' | 'warning' | 'error'
}

export default function AuditTrailPage() {
  const [filters, setFilters] = useState({
    search: '',
    dateFrom: '',
    dateTo: '',
    user: '',
    action: '',
    status: ''
  })

  // Mock audit logs data
  const logs: AuditLog[] = [
    {
      id: '1',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      user: 'admin',
      action: 'LOGIN',
      resource: 'Auth System',
      details: 'Successful login from dashboard',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      user: 'user123',
      action: 'CREATE_DOCUMENT',
      resource: 'Document #1234',
      details: 'Created new document "Project Plan"',
      ip: '192.168.1.105',
      status: 'success'
    },
    {
      id: '3',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      user: 'admin',
      action: 'DELETE_DOCUMENT',
      resource: 'Document #5678',
      details: 'Deleted document "Old Report"',
      ip: '192.168.1.100',
      status: 'warning'
    },
    {
      id: '4',
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
      user: 'user456',
      action: 'FAILED_LOGIN',
      resource: 'Auth System',
      details: 'Failed login attempt - invalid password',
      ip: '203.0.113.42',
      status: 'error'
    },
    {
      id: '5',
      timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      user: 'admin',
      action: 'UPDATE_SETTINGS',
      resource: 'System Settings',
      details: 'Updated security settings',
      ip: '192.168.1.100',
      status: 'success'
    },
    {
      id: '6',
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      user: 'user789',
      action: 'EXPORT_DATA',
      resource: 'Documents Export',
      details: 'Exported 150 documents to CSV',
      ip: '192.168.1.110',
      status: 'success'
    }
  ]

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      success: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800'
    }
    return styles[status as keyof typeof styles] || styles.success
  }

  const getStatusIcon = (status: string) => {
    if (status === 'error') return <AlertCircle className="w-4 h-4" />
    if (status === 'warning') return <AlertCircle className="w-4 h-4" />
    return null
  }

  const handleExport = () => {
    const csv = [
      ['Timestamp', 'User', 'Action', 'Resource', 'Details', 'IP', 'Status'].join(','),
      ...logs.map(log =>
        [log.timestamp, log.user, log.action, log.resource, log.details, log.ip, log.status].join(',')
      )
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_trail_${Date.now()}.csv`
    a.click()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Журнал аудита</h1>
          <p className="text-gray-600 mt-1">Полная история действий пользователей в системе</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Download className="w-4 h-4" />
          Экспорт
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <h2 className="font-semibold text-gray-900">Фильтры</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по логам..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Date From */}
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Date To */}
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* User Filter */}
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filters.user}
              onChange={(e) => setFilters({ ...filters, user: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все пользователи</option>
              <option value="admin">admin</option>
              <option value="user123">user123</option>
              <option value="user456">user456</option>
              <option value="user789">user789</option>
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <select
              value={filters.action}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все действия</option>
              <option value="LOGIN">Вход</option>
              <option value="LOGOUT">Выход</option>
              <option value="CREATE">Создание</option>
              <option value="UPDATE">Обновление</option>
              <option value="DELETE">Удаление</option>
              <option value="EXPORT">Экспорт</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Все статусы</option>
              <option value="success">Успех</option>
              <option value="warning">Предупреждение</option>
              <option value="error">Ошибка</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Время
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Пользователь
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Действие
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ресурс
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP адрес
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Статус
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatTime(log.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">{log.user}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900 font-mono">{log.action}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div>
                        <div className="text-sm text-gray-900">{log.resource}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{log.details}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                    {log.ip}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      {getStatusIcon(log.status)}
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(log.status)}`}>
                        {log.status === 'success' ? 'Успех' : log.status === 'warning' ? 'Предупр.' : 'Ошибка'}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Всего записей</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{logs.length}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Успешных</div>
          <div className="text-2xl font-bold text-green-600 mt-1">
            {logs.filter(l => l.status === 'success').length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Предупреждений</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">
            {logs.filter(l => l.status === 'warning').length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Ошибок</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {logs.filter(l => l.status === 'error').length}
          </div>
        </div>
      </div>
    </div>
  )
}
