/**
 * ActivityFeedPage - Team activity feed and timeline
 */
import { useState } from 'react'
import { FileText, MessageSquare, CheckCircle, Upload, Edit, User, Clock, Filter } from 'lucide-react'

interface Activity {
  id: string
  type: 'document_created' | 'document_edited' | 'comment_added' | 'task_completed' | 'document_uploaded' | 'approval_requested'
  user: string
  userAvatar?: string
  action: string
  target: string
  timestamp: string
  details?: string
}

export default function ActivityFeedPage() {
  const [filter, setFilter] = useState<'all' | 'documents' | 'tasks' | 'comments'>('all')
  const [activities] = useState<Activity[]>([
    {
      id: '1',
      type: 'document_created',
      user: 'Иван Петров',
      action: 'создал документ',
      target: 'Техническая спецификация v2.1',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      details: 'Начальная версия документа с основными разделами'
    },
    {
      id: '2',
      type: 'comment_added',
      user: 'Мария Сидорова',
      action: 'добавила комментарий к',
      target: 'План миграции данных',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      details: 'Предлагаю добавить этап тестирования'
    },
    {
      id: '3',
      type: 'task_completed',
      user: 'Александр Кузнецов',
      action: 'выполнил задачу',
      target: 'Подготовить презентацию для клиента',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '4',
      type: 'document_edited',
      user: 'Елена Новикова',
      action: 'отредактировала',
      target: 'Руководство пользователя',
      timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      details: 'Обновлён раздел 5: добавлены скриншоты'
    },
    {
      id: '5',
      type: 'approval_requested',
      user: 'Иван Петров',
      action: 'запросил согласование',
      target: 'Политика безопасности',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '6',
      type: 'document_uploaded',
      user: 'Мария Сидорова',
      action: 'загрузила документ',
      target: 'Архитектура системы.pdf',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      details: 'Размер: 2.5 MB'
    },
    {
      id: '7',
      type: 'comment_added',
      user: 'Александр Кузнецов',
      action: 'добавил комментарий к',
      target: 'Техническая спецификация v2.0',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      details: 'Необходимо уточнить требования к производительности'
    },
    {
      id: '8',
      type: 'task_completed',
      user: 'Елена Новикова',
      action: 'выполнила задачу',
      target: 'Обновить руководство пользователя',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '9',
      type: 'document_edited',
      user: 'Иван Петров',
      action: 'отредактировал',
      target: 'План миграции данных',
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      details: 'Добавлен раздел "Откат изменений"'
    },
    {
      id: '10',
      type: 'document_created',
      user: 'Мария Сидорова',
      action: 'создала документ',
      target: 'Инструкция по развёртыванию',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
    }
  ])

  const filteredActivities = activities.filter(activity => {
    if (filter === 'all') return true
    if (filter === 'documents') return ['document_created', 'document_edited', 'document_uploaded'].includes(activity.type)
    if (filter === 'tasks') return activity.type === 'task_completed'
    if (filter === 'comments') return activity.type === 'comment_added'
    return true
  })

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const diff = Date.now() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    if (minutes < 60) return `${minutes} мин назад`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} ч назад`
    const days = Math.floor(hours / 24)
    if (days === 1) return 'вчера'
    if (days < 7) return `${days} дн назад`
    return date.toLocaleDateString('ru-RU')
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'document_created':
      case 'document_edited':
        return <FileText className="w-5 h-5" />
      case 'document_uploaded':
        return <Upload className="w-5 h-5" />
      case 'comment_added':
        return <MessageSquare className="w-5 h-5" />
      case 'task_completed':
        return <CheckCircle className="w-5 h-5" />
      case 'approval_requested':
        return <Edit className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'document_created':
        return 'bg-green-100 text-green-600'
      case 'document_edited':
        return 'bg-blue-100 text-blue-600'
      case 'document_uploaded':
        return 'bg-purple-100 text-purple-600'
      case 'comment_added':
        return 'bg-yellow-100 text-yellow-600'
      case 'task_completed':
        return 'bg-green-100 text-green-600'
      case 'approval_requested':
        return 'bg-orange-100 text-orange-600'
      default:
        return 'bg-gray-100 text-gray-600'
    }
  }

  const documentActivities = activities.filter(a => ['document_created', 'document_edited', 'document_uploaded'].includes(a.type)).length
  const taskActivities = activities.filter(a => a.type === 'task_completed').length
  const commentActivities = activities.filter(a => a.type === 'comment_added').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Лента активности</h1>
        <p className="text-gray-600 mt-1">Отслеживание действий команды</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Всего событий</div>
          <div className="text-2xl font-bold mt-1">{activities.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Документы</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{documentActivities}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Задачи</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{taskActivities}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Комментарии</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">{commentActivities}</div>
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
              <option value="all">Все события</option>
              <option value="documents">Документы</option>
              <option value="tasks">Задачи</option>
              <option value="comments">Комментарии</option>
            </select>
          </div>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            {filteredActivities.map((activity, index) => (
              <div key={activity.id} className="flex gap-4">
                {/* Timeline line */}
                <div className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getActivityColor(activity.type)}`}>
                    {getActivityIcon(activity.type)}
                  </div>
                  {index < filteredActivities.length - 1 && (
                    <div className="w-0.5 h-full bg-gray-200 mt-2" />
                  )}
                </div>

                {/* Activity content */}
                <div className="flex-1 pb-8">
                  <div className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-primary-600" />
                        </div>
                        <div>
                          <span className="font-medium text-gray-900">{activity.user}</span>
                          <span className="text-gray-600 ml-2">{activity.action}</span>
                          <a href="#" className="text-primary-600 hover:underline ml-1">{activity.target}</a>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500 flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(activity.timestamp)}
                      </span>
                    </div>
                    {activity.details && (
                      <div className="text-sm text-gray-600 ml-10">{activity.details}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
