/**
 * Document Search Page
 */
import { useState } from 'react'
import { Search, Loader2, FileText, Filter } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface SearchResult {
  id: string
  title: string
  content: string
  category?: string
  tags?: string[]
  created_at: string
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    try {
      setLoading(true)
      setHasSearched(true)
      const data = await api.search(query.trim(), {
        limit: 50,
        category: category || undefined
      })
      setResults(data.results || data.items || [])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Search className="w-8 h-8 text-primary-600" />
          Поиск документов
        </h1>
        <p className="text-gray-600 mt-1">Поиск по названию, содержимому и тегам</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Введите поисковый запрос..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Поиск...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Искать
              </>
            )}
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Категория:</label>
          </div>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">Все категории</option>
            <option value="tutorial">Tutorial</option>
            <option value="documentation">Documentation</option>
            <option value="research">Research</option>
            <option value="note">Note</option>
          </select>
        </div>
      </form>

      {/* Results */}
      {hasSearched && (
        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            Найдено результатов: {results.length}
          </div>

          {results.length > 0 ? (
            <div className="space-y-3">
              {results.map((result) => (
                <div key={result.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition">
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-primary-600 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1">{result.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-2 mb-2">{result.content}</p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        {result.category && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                            {result.category}
                          </span>
                        )}
                        {result.tags && result.tags.length > 0 && (
                          <div className="flex gap-1">
                            {result.tags.slice(0, 3).map((tag, idx) => (
                              <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-600 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <span>{new Date(result.created_at).toLocaleDateString('ru-RU')}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Ничего не найдено</p>
              <p className="text-sm text-gray-500 mt-1">Попробуйте изменить запрос</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
