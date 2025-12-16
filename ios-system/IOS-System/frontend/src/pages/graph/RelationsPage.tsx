/**
 * Relations Browser Page
 */
import { useEffect, useState } from 'react'
import { Network, Loader2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

interface Relation {
  id: string
  source: string
  target: string
  type: string
  confidence: number
}

export default function RelationsPage() {
  const [loading, setLoading] = useState(true)
  const [relations, setRelations] = useState<Relation[]>([])

  useEffect(() => {
    fetchRelations()
  }, [])

  const fetchRelations = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/graph/relations')
      setRelations(response.data.relations || [])
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load relations')
    } finally {
      setLoading(false)
    }
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Network className="w-8 h-8 text-primary-600" />
          Связи
        </h1>
        <p className="text-gray-600 mt-1">Все связи между сущностями в графе знаний</p>
      </div>

      {/* Relations List */}
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {relations.length > 0 ? (
          relations.map((relation) => (
            <div key={relation.id} className="p-4 hover:bg-gray-50 transition">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">{relation.source}</span>
                    <span className="text-gray-500">→</span>
                    <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm font-medium">
                      {relation.type}
                    </span>
                    <span className="text-gray-500">→</span>
                    <span className="font-semibold text-gray-900">{relation.target}</span>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  Уверенность: {(relation.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Связи не найдены</p>
          </div>
        )}
      </div>
    </div>
  )
}
