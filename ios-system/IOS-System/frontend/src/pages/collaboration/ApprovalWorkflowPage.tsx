/**
 * ApprovalWorkflowPage - Document approval workflow management
 */
import { useState } from 'react'
import { CheckCircle, XCircle, Clock, User, FileText, AlertCircle, Filter } from 'lucide-react'
import { toast } from 'sonner'

interface ApprovalRequest {
  id: string
  documentId: string
  documentTitle: string
  requestedBy: string
  assignedTo: string
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  priority: 'low' | 'medium' | 'high'
  createdAt: string
  dueDate: string
  comments?: string
}

export default function ApprovalWorkflowPage() {
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending')
  const [requests] = useState<ApprovalRequest[]>([
    {
      id: '1',
      documentId: 'doc-123',
      documentTitle: 'Техническая спецификация v2.0',
      requestedBy: 'Иван Петров',
      assignedTo: 'Мария Сидорова',
      status: 'pending',
      priority: 'high',
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '2',
      documentId: 'doc-456',
      documentTitle: 'План миграции данных',
      requestedBy: 'Александр Кузнецов',
      assignedTo: 'Елена Новикова',
      status: 'pending',
      priority: 'medium',
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '3',
      documentId: 'doc-789',
      documentTitle: 'Политика безопасности',
      requestedBy: 'Мария Сидорова',
      assignedTo: 'Иван Петров',
      status: 'approved',
      priority: 'high',
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      comments: 'Утверждено без замечаний'
    },
    {
      id: '4',
      documentId: 'doc-321',
      documentTitle: 'Руководство пользователя',
      requestedBy: 'Елена Новикова',
      assignedTo: 'Александр Кузнецов',
      status: 'rejected',
      priority: 'low',
      createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      comments: 'Требуется доработка раздела 5'
    },
    {
      id: '5',
      documentId: 'doc-654',
      documentTitle: 'Инструкция по развёртыванию',
      requestedBy: 'Иван Петров',
      assignedTo: 'Мария Сидорова',
      status: 'pending',
      priority: 'high',
      createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString()
    }
  ])

  const filteredRequests = requests.filter(req => {
    if (filter === 'all') return true
    return req.status === filter
  })

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const diff = Date.now() - date.getTime()
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (hours < 24) return `${hours} ч назад`
    const days = Math.floor(hours / 24)
    if (days === 1) return 'вчера'
    if (days < 7) return `${days} дн назад`
    return date.toLocaleDateString('ru-RU')
  }

  const formatDueDate = (timestamp: string) => {
    const date = new Date(timestamp)
    const diff = date.getTime() - Date.now()
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (diff < 0) return 'Просрочено'
    if (hours < 24) return `через ${hours} ч`
    const days = Math.floor(hours / 24)
    return `через ${days} дн`
  }

  const handleApprove = (_requestId: string) => {
    toast.success('Документ утверждён')
  }

  const handleReject = (_requestId: string) => {
    toast.error('Документ отклонён')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'approved': return 'bg-green-100 text-green-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      case 'expired': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600'
      case 'medium': return 'text-yellow-600'
      case 'low': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  const getDueDateColor = (dueDate: string) => {
    const diff = new Date(dueDate).getTime() - Date.now()
    const hours = Math.floor(diff / (60 * 60 * 1000))
    if (diff < 0) return 'text-red-600'
    if (hours < 24) return 'text-orange-600'
    return 'text-gray-600'
  }

  const pendingCount = requests.filter(r => r.status === 'pending').length
  const approvedCount = requests.filter(r => r.status === 'approved').length
  const rejectedCount = requests.filter(r => r.status === 'rejected').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Согласование документов</h1>
          <p className="text-gray-600 mt-1">Управление запросами на утверждение</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Всего запросов</div>
          <div className="text-2xl font-bold mt-1">{requests.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">На согласовании</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">{pendingCount}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Утверждённых</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{approvedCount}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Отклонённых</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{rejectedCount}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <span className="font-medium text-gray-900">Фильтр:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="px-3 py-1 border rounded-lg text-sm"
            >
              <option value="all">Все</option>
              <option value="pending">На согласовании</option>
              <option value="approved">Утверждённые</option>
              <option value="rejected">Отклонённые</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Документ</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Инициатор</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Согласующий</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Приоритет</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Срок</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredRequests.map(request => (
                <tr key={request.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <div>
                        <div className="font-medium text-gray-900">{request.documentTitle}</div>
                        <div className="text-xs text-gray-500">{formatTime(request.createdAt)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-gray-900">
                      <User className="w-4 h-4 text-gray-400" />
                      {request.requestedBy}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-gray-900">
                      <User className="w-4 h-4 text-gray-400" />
                      {request.assignedTo}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-sm font-medium ${getPriorityColor(request.priority)}`}>
                      {request.priority === 'high' ? 'Высокий' : request.priority === 'medium' ? 'Средний' : 'Низкий'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className={`text-sm flex items-center gap-1 ${getDueDateColor(request.dueDate)}`}>
                      <Clock className="w-4 h-4" />
                      {formatDueDate(request.dueDate)}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(request.status)}`}>
                      {request.status === 'pending' ? 'Ожидает' : request.status === 'approved' ? 'Утверждён' : 'Отклонён'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {request.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprove(request.id)}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="Утвердить"
                        >
                          <CheckCircle className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleReject(request.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="Отклонить"
                        >
                          <XCircle className="w-5 h-5" />
                        </button>
                      </div>
                    )}
                    {request.comments && (
                      <div className="text-xs text-gray-500 mt-1">{request.comments}</div>
                    )}
                  </td>
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
            <p className="font-medium mb-1">Workflow согласования</p>
            <p>Используйте систему согласования для контроля качества документов перед публикацией. Просроченные запросы требуют немедленного внимания.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
