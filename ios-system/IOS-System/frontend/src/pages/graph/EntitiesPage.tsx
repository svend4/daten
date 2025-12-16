/**
 * Entities Browser Page
 */
import { useEffect, useState } from 'react'
import { Database, Loader2, AlertCircle, Search } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface Entity {
  id: string
  name: string
  type: string
  occurrences: number
}

export default function EntitiesPage() {
  const [loading, setLoading] = useState(true)
  const [entities, setEntities] = useState<Entity[]>([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchEntities()
  }, [])

  const fetchEntities = async () => {
    try {
      setLoading(true)
      const data = await api.getGraphEntities()
      setEntities(data.entities || [])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load entities')
    } finally {
      setLoading(false)
    }
  }

  const filteredEntities = entities.filter((entity) =>
    entity.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Database className="w-8 h-8 text-primary-600" />
          Сущности
        </h1>
        <p className="text-gray-600 mt-1">Все извлеченные сущности из документов</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Поиск сущностей..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Entities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEntities.length > 0 ? (
          filteredEntities.map((entity) => (
            <div key={entity.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition">
              <div className="font-semibold text-gray-900">{entity.name}</div>
              <div className="text-sm text-gray-500 mt-1">Тип: {entity.type}</div>
              <div className="text-xs text-gray-400 mt-2">
                Встречается: {entity.occurrences} раз
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Сущности не найдены</p>
          </div>
        )}
      </div>
    </div>
  )
}
