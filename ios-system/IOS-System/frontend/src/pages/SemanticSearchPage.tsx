/**
 * Semantic Search Page
 */
import { useState } from 'react'
import { Sparkles, Search, Loader2, FileText } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

interface SearchResult {
  id: string
  title: string
  content: string
  score: number
}

export default function SemanticSearchPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    try {
      setLoading(true)
      setHasSearched(true)
      const response = await apiClient.post('/search', {
        query: query.trim(),
        semantic: true,
        limit: 20,
      })
      setResults(response.data.results || [])
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
          <Sparkles className="w-8 h-8 text-primary-600" />
          Семантический поиск
        </h1>
        <p className="text-gray-600 mt-1">Интеллектуальный поиск по смыслу, а не по ключевым словам</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Введите запрос для семантического поиска..."
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
                <Sparkles className="w-5 h-5" />
                Искать
              </>
            )}
          </button>
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
                      <p className="text-sm text-gray-600 line-clamp-2">{result.content}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="text-xs text-gray-500">
                          Релевантность: {(result.score * 100).toFixed(0)}%
                        </div>
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
            </div>
          )}
        </div>
      )}
    </div>
  )
}
