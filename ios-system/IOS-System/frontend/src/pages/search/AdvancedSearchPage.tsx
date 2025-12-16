/**
 * Advanced Search Page - Search with advanced filters
 */
import { useState } from 'react'
import { SlidersHorizontal, Search, Loader2, FileText, Calendar, Tag } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

export default function AdvancedSearchPage() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])
  const [filters, setFilters] = useState({
    query: '',
    category: '',
    tags: '',
    dateFrom: '',
    dateTo: '',
    minLength: '',
    maxLength: ''
  })

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!filters.query.trim()) {
      toast.error('Введите поисковый запрос')
      return
    }

    try {
      setLoading(true)
      const params: any = { q: filters.query }
      if (filters.category) params.category = filters.category

      const data = await api.search(filters.query, params)
      let filteredResults = data.results || data.items || []

      // Apply client-side filters
      if (filters.tags) {
        const searchTags = filters.tags.split(',').map(t => t.trim().toLowerCase())
        filteredResults = filteredResults.filter((r: any) =>
          r.tags?.some((t: string) => searchTags.some(st => t.toLowerCase().includes(st)))
        )
      }

      if (filters.dateFrom) {
        const fromDate = new Date(filters.dateFrom)
        filteredResults = filteredResults.filter((r: any) =>
          new Date(r.created_at) >= fromDate
        )
      }

      if (filters.dateTo) {
        const toDate = new Date(filters.dateTo)
        filteredResults = filteredResults.filter((r: any) =>
          new Date(r.created_at) <= toDate
        )
      }

      setResults(filteredResults)
      toast.success(`Найдено: ${filteredResults.length}`)
    } catch (err: any) {
      toast.error('Ошибка поиска')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <SlidersHorizontal className="w-8 h-8 text-primary-600" />
          Расширенный поиск
        </h1>
        <p className="text-gray-600 mt-1">Поиск с детальными фильтрами</p>
      </div>

      <form onSubmit={handleSearch} className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Поисковый запрос *
            </label>
            <input
              type="text"
              value={filters.query}
              onChange={(e) => setFilters({ ...filters, query: e.target.value })}
              placeholder="Введите запрос..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Категория
            </label>
            <input
              type="text"
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              placeholder="Например: work"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Теги (через запятую)
            </label>
            <input
              type="text"
              value={filters.tags}
              onChange={(e) => setFilters({ ...filters, tags: e.target.value })}
              placeholder="Например: важно, проект"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Дата от
            </label>
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Дата до
            </label>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Поиск...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Найти
            </>
          )}
        </button>
      </form>

      {results.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">
              Результаты ({results.length})
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {results.map((result) => (
              <div key={result.id} className="p-6">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-primary-600 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">{result.title}</h3>
                    <p className="text-gray-600 text-sm line-clamp-2 mb-2">{result.content}</p>
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
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
