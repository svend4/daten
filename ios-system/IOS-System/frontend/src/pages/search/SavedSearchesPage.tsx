/**
 * Saved Searches Page - Manage saved search queries
 */
import { useState, useEffect } from 'react'
import { Bookmark, Search, Trash2, Play, Plus, Calendar, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

interface SavedSearch {
  id: string
  name: string
  query: string
  filters?: {
    category?: string
    tags?: string[]
    dateFrom?: string
    dateTo?: string
  }
  created_at: string
  last_used?: string
  use_count: number
}

export default function SavedSearchesPage() {
  const navigate = useNavigate()
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [newSearch, setNewSearch] = useState({
    name: '',
    query: '',
    category: '',
    tags: ''
  })

  useEffect(() => {
    loadSavedSearches()
  }, [])

  const loadSavedSearches = () => {
    // Load from localStorage for demo
    const saved = localStorage.getItem('savedSearches')
    if (saved) {
      setSearches(JSON.parse(saved))
    } else {
      // Demo data
      const demoSearches: SavedSearch[] = [
        {
          id: '1',
          name: 'Важные документы',
          query: 'важный',
          filters: { category: 'work' },
          created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
          last_used: new Date(Date.now() - 86400000).toISOString(),
          use_count: 15
        },
        {
          id: '2',
          name: 'Проекты 2024',
          query: 'проект',
          filters: {
            tags: ['проект', '2024'],
            dateFrom: '2024-01-01'
          },
          created_at: new Date(Date.now() - 14 * 86400000).toISOString(),
          last_used: new Date(Date.now() - 2 * 86400000).toISOString(),
          use_count: 8
        },
        {
          id: '3',
          name: 'Отчёты',
          query: 'отчёт',
          filters: { category: 'reports' },
          created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
          use_count: 3
        }
      ]
      setSearches(demoSearches)
      localStorage.setItem('savedSearches', JSON.stringify(demoSearches))
    }
    setLoading(false)
  }

  const handleSaveSearch = () => {
    if (!newSearch.name.trim() || !newSearch.query.trim()) {
      toast.error('Заполните название и запрос')
      return
    }

    const search: SavedSearch = {
      id: Date.now().toString(),
      name: newSearch.name.trim(),
      query: newSearch.query.trim(),
      filters: {
        category: newSearch.category || undefined,
        tags: newSearch.tags ? newSearch.tags.split(',').map(t => t.trim()) : undefined
      },
      created_at: new Date().toISOString(),
      use_count: 0
    }

    const updated = [...searches, search]
    setSearches(updated)
    localStorage.setItem('savedSearches', JSON.stringify(updated))

    setShowAddDialog(false)
    setNewSearch({ name: '', query: '', category: '', tags: '' })
    toast.success('Поиск сохранён')
  }

  const handleRunSearch = (search: SavedSearch) => {
    // Update usage stats
    const updated = searches.map(s =>
      s.id === search.id
        ? { ...s, last_used: new Date().toISOString(), use_count: s.use_count + 1 }
        : s
    )
    setSearches(updated)
    localStorage.setItem('savedSearches', JSON.stringify(updated))

    // Navigate to search page with parameters
    const params = new URLSearchParams()
    params.set('q', search.query)
    if (search.filters?.category) params.set('category', search.filters.category)
    navigate(`/search?${params.toString()}`)
  }

  const handleDelete = (id: string) => {
    const updated = searches.filter(s => s.id !== id)
    setSearches(updated)
    localStorage.setItem('savedSearches', JSON.stringify(updated))
    toast.success('Поиск удалён')
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(date)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bookmark className="w-8 h-8 text-primary-600" />
            Сохранённые поиски
          </h1>
          <p className="text-gray-600 mt-1">Быстрый доступ к часто используемым запросам</p>
        </div>
        <button
          onClick={() => setShowAddDialog(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Добавить поиск
        </button>
      </div>

      {/* Saved Searches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {searches.map((search) => (
          <div key={search.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">{search.name}</h3>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Search className="w-4 h-4" />
                  <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
                    {search.query}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleDelete(search.id)}
                className="p-1 hover:bg-red-50 rounded text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            {/* Filters */}
            {(search.filters?.category || search.filters?.tags) && (
              <div className="mb-4 space-y-2">
                {search.filters.category && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Категория:</span> {search.filters.category}
                  </div>
                )}
                {search.filters.tags && search.filters.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {search.filters.tags.map((tag, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-primary-100 text-primary-800 text-xs rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Stats */}
            <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
              <div className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {formatDate(search.created_at)}
              </div>
              <div>Использован: {search.use_count} раз</div>
            </div>

            {search.last_used && (
              <div className="text-xs text-gray-500 mb-4">
                Последний раз: {formatDate(search.last_used)}
              </div>
            )}

            {/* Run Button */}
            <button
              onClick={() => handleRunSearch(search)}
              className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              Выполнить поиск
            </button>
          </div>
        ))}
      </div>

      {searches.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Bookmark className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">Нет сохранённых поисков</p>
          <button
            onClick={() => setShowAddDialog(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Создать первый поиск
          </button>
        </div>
      )}

      {/* Add Dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Новый сохранённый поиск</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Название *
                </label>
                <input
                  type="text"
                  value={newSearch.name}
                  onChange={(e) => setNewSearch({ ...newSearch, name: e.target.value })}
                  placeholder="Например: Важные документы"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Поисковый запрос *
                </label>
                <input
                  type="text"
                  value={newSearch.query}
                  onChange={(e) => setNewSearch({ ...newSearch, query: e.target.value })}
                  placeholder="Введите запрос"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Категория (опционально)
                </label>
                <input
                  type="text"
                  value={newSearch.category}
                  onChange={(e) => setNewSearch({ ...newSearch, category: e.target.value })}
                  placeholder="Например: work"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Теги (через запятую)
                </label>
                <input
                  type="text"
                  value={newSearch.tags}
                  onChange={(e) => setNewSearch({ ...newSearch, tags: e.target.value })}
                  placeholder="Например: проект, важно"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddDialog(false)
                  setNewSearch({ name: '', query: '', category: '', tags: '' })
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Отмена
              </button>
              <button
                onClick={handleSaveSearch}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
