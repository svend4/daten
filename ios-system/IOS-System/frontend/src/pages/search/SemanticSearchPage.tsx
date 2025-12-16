/**
 * Semantic Search Page
 */
import { useState } from 'react'
import { Sparkles, Loader2, Search, FileText, Tag, Calendar } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface SearchResult {
  id: string
  title: string
  content: string
  score?: number
  tags?: string[]
  category?: string
  created_at?: string
}

export default function SemanticSearchPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) {
      toast.error('Введите поисковый запрос')
      return
    }

    try {
      setLoading(true)
      setHasSearched(true)
      const data = await api.semanticSearch(query.trim(), { limit: 50 })
      setResults(data.results || data.items || [])

      if (!data.results?.length && !data.items?.length) {
        toast.info('Ничего не найдено')
      } else {
        toast.success(`Найдено результатов: ${data.results?.length || data.items?.length || 0}`)
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Semantic search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-primary-600" />
          Семантический поиск
        </h1>
        <p className="text-gray-600 mt-1">Интеллектуальный поиск по смыслу, а не по ключевым словам</p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Поисковый запрос
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Опишите что вы ищете..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={loading}
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
            <p className="text-sm text-gray-500 mt-2">
              Семантический поиск понимает смысл вашего запроса и находит релевантные документы
            </p>
          </div>
        </div>
      </form>

      {/* Results */}
      {hasSearched && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Результаты поиска
              {results.length > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({results.length})
                </span>
              )}
            </h2>
          </div>

          <div className="divide-y divide-gray-200">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
              </div>
            ) : results.length > 0 ? (
              results.map((result) => (
                <div key={result.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-5 h-5 text-primary-600" />
                        <h3 className="text-lg font-semibold text-gray-900">{result.title}</h3>
                        {result.score !== undefined && (
                          <span className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full font-medium">
                            {Math.round(result.score * 100)}% совпадение
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 line-clamp-3 mb-3">{result.content}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        {result.category && (
                          <span className="flex items-center gap-1">
                            <Tag className="w-4 h-4" />
                            {result.category}
                          </span>
                        )}
                        {result.created_at && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(result.created_at).toLocaleDateString('ru-RU')}
                          </span>
                        )}
                      </div>
                      {result.tags && result.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {result.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Ничего не найдено</p>
                <p className="text-sm text-gray-500 mt-1">Попробуйте изменить запрос</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
