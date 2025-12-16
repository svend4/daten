/**
 * Tag Search Page - Browse and search by tags
 */
import { useState, useEffect } from 'react'
import { Tag, Search, Loader2, FileText } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface TagInfo {
  name: string
  count: number
  color: string
}

export default function TagSearchPage() {
  const [loading, setLoading] = useState(false)
  const [tags, setTags] = useState<TagInfo[]>([])
  const [selectedTag, setSelectedTag] = useState<string | null>(null)
  const [results, setResults] = useState<any[]>([])

  useEffect(() => {
    loadTags()
  }, [])

  const loadTags = async () => {
    // Demo tags
    const demoTags: TagInfo[] = [
      { name: 'важно', count: 15, color: 'bg-red-100 text-red-800' },
      { name: 'проект', count: 12, color: 'bg-blue-100 text-blue-800' },
      { name: 'документация', count: 8, color: 'bg-green-100 text-green-800' },
      { name: '2024', count: 10, color: 'bg-purple-100 text-purple-800' },
      { name: 'отчёт', count: 6, color: 'bg-yellow-100 text-yellow-800' },
      { name: 'архив', count: 4, color: 'bg-gray-100 text-gray-800' }
    ]
    setTags(demoTags)
  }

  const handleTagClick = async (tagName: string) => {
    setSelectedTag(tagName)
    setLoading(true)

    try {
      const data = await api.search(tagName, { limit: 50 })
      const filtered = (data.results || data.items || []).filter((r: any) =>
        r.tags?.some((t: string) => t.toLowerCase() === tagName.toLowerCase())
      )
      setResults(filtered)

      if (filtered.length === 0) {
        toast.info('Документы с этим тегом не найдены')
      }
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
          <Tag className="w-8 h-8 text-primary-600" />
          Поиск по тегам
        </h1>
        <p className="text-gray-600 mt-1">Просмотр документов по тегам</p>
      </div>

      {/* Tags Cloud */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Популярные теги</h2>
        <div className="flex flex-wrap gap-3">
          {tags.map((tag) => (
            <button
              key={tag.name}
              onClick={() => handleTagClick(tag.name)}
              className={`px-4 py-2 rounded-full font-medium transition-all ${
                selectedTag === tag.name
                  ? 'ring-2 ring-primary-500'
                  : ''
              } ${tag.color} hover:scale-105`}
            >
              #{tag.name}
              <span className="ml-2 text-xs opacity-75">({tag.count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {selectedTag && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">
              Документы с тегом "#{selectedTag}"
              {!loading && results.length > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({results.length})
                </span>
              )}
            </h2>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            </div>
          ) : results.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {results.map((result) => (
                <div key={result.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-primary-600 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 mb-1">{result.title}</h3>
                      <p className="text-gray-600 text-sm line-clamp-2 mb-2">{result.content}</p>
                      {result.tags && result.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {result.tags.map((t: string, idx: number) => (
                            <span
                              key={idx}
                              onClick={(e) => {
                                e.stopPropagation()
                                handleTagClick(t)
                              }}
                              className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full cursor-pointer hover:bg-gray-200"
                            >
                              #{t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Документы не найдены</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
