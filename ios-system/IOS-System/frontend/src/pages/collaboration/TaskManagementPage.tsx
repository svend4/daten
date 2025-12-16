/**
 * TaskManagementPage - Task management and tracking
 */
import { useState } from 'react'
import { CheckSquare, Square, Clock, User, Plus, Calendar, Flag, Filter } from 'lucide-react'
import { toast } from 'sonner'

interface Task {
  id: string
  title: string
  description: string
  assignedTo: string
  createdBy: string
  status: 'todo' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
  dueDate: string
  createdAt: string
  relatedDocument?: string
}

export default function TaskManagementPage() {
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'completed'>('all')
  const [tasks] = useState<Task[]>([
    {
      id: '1',
      title: 'Обновить техническую документацию',
      description: 'Добавить описание новых API endpoints в раздел 4.2',
      assignedTo: 'Иван Петров',
      createdBy: 'Мария Сидорова',
      status: 'in_progress',
      priority: 'high',
      dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
      relatedDocument: 'Техническая спецификация v2.0'
    },
    {
      id: '2',
      title: 'Провести ревью безопасности',
      description: 'Проверить политику доступа к конфиденциальным данным',
      assignedTo: 'Александр Кузнецов',
      createdBy: 'Елена Новикова',
      status: 'todo',
      priority: 'high',
      dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      relatedDocument: 'Политика безопасности'
    },
    {
      id: '3',
      title: 'Обновить руководство пользователя',
      description: 'Добавить скриншоты для раздела 5 и 6',
      assignedTo: 'Елена Новикова',
      createdBy: 'Иван Петров',
      status: 'todo',
      priority: 'medium',
      dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      relatedDocument: 'Руководство пользователя'
    },
    {
      id: '4',
      title: 'Подготовить презентацию для клиента',
      description: 'Создать слайды с основными возможностями системы',
      assignedTo: 'Мария Сидорова',
      createdBy: 'Александр Кузнецов',
      status: 'completed',
      priority: 'medium',
      dueDate: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '5',
      title: 'Составить план миграции',
      description: 'Разработать детальный план переноса данных из старой системы',
      assignedTo: 'Иван Петров',
      createdBy: 'Мария Сидорова',
      status: 'in_progress',
      priority: 'high',
      dueDate: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      relatedDocument: 'План миграции данных'
    }
  ])

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true
    return task.status === filter
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
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    if (diff < 0) return 'Просрочено'
    if (days === 0) return 'Сегодня'
    if (days === 1) return 'Завтра'
    return date.toLocaleDateString('ru-RU')
  }

  const handleToggleStatus = (_taskId: string, currentStatus: string) => {
    if (currentStatus === 'completed') {
      toast.info('Задача отмечена как активная')
    } else {
      toast.success('Задача выполнена!')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'todo': return 'bg-gray-100 text-gray-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
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
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    if (diff < 0) return 'text-red-600'
    if (days <= 1) return 'text-orange-600'
    return 'text-gray-600'
  }

  const todoCount = tasks.filter(t => t.status === 'todo').length
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length
  const completedCount = tasks.filter(t => t.status === 'completed').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Управление задачами</h1>
          <p className="text-gray-600 mt-1">Отслеживание задач команды</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          <Plus className="w-4 h-4" />
          Создать задачу
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Всего задач</div>
          <div className="text-2xl font-bold mt-1">{tasks.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">К выполнению</div>
          <div className="text-2xl font-bold text-gray-600 mt-1">{todoCount}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">В работе</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{inProgressCount}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Завершённых</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{completedCount}</div>
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
              <option value="todo">К выполнению</option>
              <option value="in_progress">В работе</option>
              <option value="completed">Завершённые</option>
            </select>
          </div>
        </div>

        <div className="divide-y">
          {filteredTasks.map((task) => (
            <div key={task.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-start gap-4">
                <button
                  onClick={() => handleToggleStatus(task.id, task.status)}
                  className="flex-shrink-0 mt-1"
                >
                  {task.status === 'completed' ? (
                    <CheckSquare className="w-5 h-5 text-green-600" />
                  ) : (
                    <Square className="w-5 h-5 text-gray-400 hover:text-primary-600" />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className={`font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                      {task.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(task.status)}`}>
                      {task.status === 'todo' ? 'К выполнению' : task.status === 'in_progress' ? 'В работе' : 'Завершено'}
                    </span>
                    <span className={`flex items-center gap-1 text-sm font-medium ${getPriorityColor(task.priority)}`}>
                      <Flag className="w-4 h-4" />
                      {task.priority === 'high' ? 'Высокий' : task.priority === 'medium' ? 'Средний' : 'Низкий'}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">{task.description}</p>

                  {task.relatedDocument && (
                    <div className="text-sm text-gray-600 mb-2">
                      Связан с: <a href="#" className="text-primary-600 hover:underline">{task.relatedDocument}</a>
                    </div>
                  )}

                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      {task.assignedTo}
                    </span>
                    <span className={`flex items-center gap-1 ${getDueDateColor(task.dueDate)}`}>
                      <Calendar className="w-4 h-4" />
                      {formatDueDate(task.dueDate)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      Создана {formatTime(task.createdAt)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
