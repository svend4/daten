/**
 * Search History Page - View recent search queries
 */
import { useState, useEffect } from 'react'
import { Clock, Search, Trash2, Play, X } from 'lucide-react'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

interface SearchHistoryItem {
  id: string
  query: string
  timestamp: string
  results_count?: number
}

export default function SearchHistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<SearchHistoryItem[]>([])

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = () => {
    const saved = localStorage.getItem('searchHistory')
    if (saved) {
      setHistory(JSON.parse(saved))
    } else {
      // Demo data
      const demoHistory: SearchHistoryItem[] = [
        { id: '1', query: 'важный документ', timestamp: new Date(Date.now() - 3600000).toISOString(), results_count: 5 },
        { id: '2', query: 'проект 2024', timestamp: new Date(Date.now() - 7200000).toISOString(), results_count: 12 },
        { id: '3', query: 'отчёт', timestamp: new Date(Date.now() - 86400000).toISOString(), results_count: 3 }
      ]
      setHistory(demoHistory)
      localStorage.setItem('searchHistory', JSON.stringify(demoHistory))
    }
  }

  const handleRunSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`)
  }

  const handleDelete = (id: string) => {
    const updated = history.filter(h => h.id !== id)
    setHistory(updated)
    localStorage.setItem('searchHistory', JSON.stringify(updated))
    toast.success('Запись удалена')
  }

  const handleClearAll = () => {
    setHistory([])
    localStorage.removeItem('searchHistory')
    toast.success('История очищена')
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / 3600000)
    if (hours < 1) return 'Только что'
    if (hours < 24) return `${hours}ч назад`
    const days = Math.floor(hours / 24)
    return `${days}д назад`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Clock className="w-8 h-8 text-primary-600" />
            История поиска
          </h1>
          <p className="text-gray-600 mt-1">Ваши последние поисковые запросы</p>
        </div>
        {history.length > 0 && (
          <button
            onClick={handleClearAll}
            className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Очистить всё
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {history.length > 0 ? (
          history.map((item) => (
            <div key={item.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
              <div className="flex items-center gap-4 flex-1">
                <Search className="w-5 h-5 text-gray-400" />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{item.query}</div>
                  <div className="text-sm text-gray-500">
                    {formatTime(item.timestamp)}
                    {item.results_count !== undefined && ` • ${item.results_count} результатов`}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleRunSearch(item.query)}
                  className="p-2 text-primary-600 hover:bg-primary-50 rounded"
                >
                  <Play className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">История поиска пуста</p>
          </div>
        )}
      </div>
    </div>
  )
}
