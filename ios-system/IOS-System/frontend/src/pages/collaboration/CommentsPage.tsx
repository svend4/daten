/**
 * CommentsPage - Comments and discussions management
 */
import { useState } from 'react'
import { Reply, ThumbsUp, AlertCircle, User, Clock, Filter } from 'lucide-react'
import { toast } from 'sonner'

interface Comment {
  id: string
  documentId: string
  documentTitle: string
  author: string
  authorAvatar?: string
  content: string
  createdAt: string
  replies: number
  likes: number
  isResolved: boolean
  status: 'open' | 'resolved' | 'archived'
}

export default function CommentsPage() {
  const [filter, setFilter] = useState<'all' | 'open' | 'resolved'>('all')
  const [comments] = useState<Comment[]>([
    {
      id: '1',
      documentId: 'doc-123',
      documentTitle: 'Техническая спецификация v2.0',
      author: 'Иван Петров',
      content: 'Необходимо уточнить требования к производительности в разделе 3.2',
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      replies: 3,
      likes: 5,
      isResolved: false,
      status: 'open'
    },
    {
      id: '2',
      documentId: 'doc-456',
      documentTitle: 'План миграции данных',
      author: 'Мария Сидорова',
      content: 'Предлагаю добавить этап тестирования перед финальной миграцией',
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      replies: 8,
      likes: 12,
      isResolved: false,
      status: 'open'
    },
    {
      id: '3',
      documentId: 'doc-789',
      documentTitle: 'Политика безопасности',
      author: 'Александр Кузнецов',
      content: 'Раздел о парольной политике устарел, нужно обновить согласно новым стандартам',
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      replies: 2,
      likes: 8,
      isResolved: true,
      status: 'resolved'
    },
    {
      id: '4',
      documentId: 'doc-321',
      documentTitle: 'Руководство пользователя',
      author: 'Елена Новикова',
      content: 'В разделе 5 не хватает скриншотов для наглядности',
      createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      replies: 1,
      likes: 3,
      isResolved: false,
      status: 'open'
    }
  ])

  const filteredComments = comments.filter(comment => {
    if (filter === 'all') return true
    return comment.status === filter
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

  const handleResolve = (_commentId: string) => {
    toast.success('Обсуждение отмечено как решённое')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800'
      case 'resolved': return 'bg-green-100 text-green-800'
      case 'archived': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const openComments = comments.filter(c => c.status === 'open').length
  const resolvedComments = comments.filter(c => c.status === 'resolved').length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Комментарии и обсуждения</h1>
          <p className="text-gray-600 mt-1">Управление комментариями к документам</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Всего обсуждений</div>
          <div className="text-2xl font-bold mt-1">{comments.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Открытых</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{openComments}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Решённых</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{resolvedComments}</div>
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
              <option value="open">Открытые</option>
              <option value="resolved">Решённые</option>
            </select>
          </div>
        </div>

        <div className="divide-y">
          {filteredComments.map((comment) => (
            <div key={comment.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-primary-600" />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-medium text-gray-900">{comment.author}</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(comment.status)}`}>
                      {comment.status === 'open' ? 'Открыто' : 'Решено'}
                    </span>
                    <span className="text-sm text-gray-500 flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {formatTime(comment.createdAt)}
                    </span>
                  </div>

                  <div className="text-sm text-gray-600 mb-2">
                    Документ: <a href="#" className="text-primary-600 hover:underline">{comment.documentTitle}</a>
                  </div>

                  <p className="text-gray-900 mb-3">{comment.content}</p>

                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <button className="flex items-center gap-1 hover:text-primary-600">
                      <Reply className="w-4 h-4" />
                      <span>{comment.replies} ответов</span>
                    </button>
                    <button className="flex items-center gap-1 hover:text-primary-600">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{comment.likes}</span>
                    </button>
                    {!comment.isResolved && (
                      <button
                        onClick={() => handleResolve(comment.id)}
                        className="text-green-600 hover:text-green-700"
                      >
                        Отметить как решённое
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Система комментариев</p>
            <p>Комментарии помогают команде обсуждать документы и отслеживать изменения. Используйте статус "Решено" для завершённых обсуждений.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
