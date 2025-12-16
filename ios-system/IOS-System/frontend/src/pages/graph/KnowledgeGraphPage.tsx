/**
 * Knowledge Graph Visualization Page
 */
import { useEffect, useState } from 'react'
import { Network, Loader2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

interface GraphNode {
  id: string
  label: string
  type: string
}

interface GraphEdge {
  source: string
  target: string
  label: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export default function KnowledgeGraphPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)

  useEffect(() => {
    fetchGraphData()
  }, [])

  const fetchGraphData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.get('/graph')
      setGraphData(response.data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load knowledge graph'
      setError(errorMessage)
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Загрузка графа знаний...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Ошибка загрузки</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchGraphData}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Network className="w-8 h-8 text-primary-600" />
            Граф знаний
          </h1>
          <p className="text-gray-600 mt-1">Визуализация связей между документами и сущностями</p>
        </div>
        <button
          onClick={fetchGraphData}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Обновить
        </button>
      </div>

      {/* Graph Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm font-medium text-gray-600">Узлы (Nodes)</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {graphData?.nodes?.length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm font-medium text-gray-600">Связи (Edges)</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {graphData?.edges?.length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm font-medium text-gray-600">Плотность</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {graphData?.nodes && graphData.nodes.length > 0
              ? ((graphData.edges?.length || 0) / graphData.nodes.length).toFixed(2)
              : '0'}
          </div>
        </div>
      </div>

      {/* Graph Visualization Placeholder */}
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="text-center">
          <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Визуализация графа
          </h3>
          <p className="text-gray-600 mb-6">
            Для полноценной визуализации графа можно интегрировать библиотеку вроде D3.js, Cytoscape.js или React Flow
          </p>

          {/* Nodes List */}
          {graphData && graphData.nodes && graphData.nodes.length > 0 && (
            <div className="mt-8 text-left">
              <h4 className="font-semibold text-gray-900 mb-4">Узлы графа:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {graphData.nodes.map((node) => (
                  <div
                    key={node.id}
                    className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="text-sm font-medium text-gray-900">{node.label}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Тип: {node.type}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Edges List */}
          {graphData && graphData.edges && graphData.edges.length > 0 && (
            <div className="mt-8 text-left">
              <h4 className="font-semibold text-gray-900 mb-4">Связи:</h4>
              <div className="space-y-2">
                {graphData.edges.map((edge, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm"
                  >
                    <span className="font-medium text-gray-900">{edge.source}</span>
                    <span className="text-gray-500 mx-2">→ ({edge.label}) →</span>
                    <span className="font-medium text-gray-900">{edge.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!graphData || (graphData.nodes.length === 0 && graphData.edges.length === 0)) && (
            <p className="text-gray-500 italic mt-4">
              Граф пуст. Создайте документы для построения графа знаний.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
