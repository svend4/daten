/**
 * AI Entity Extraction Page
 */
import { useState } from 'react'
import { Sparkles, Loader2, Database } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface Entity {
  text: string
  type: string
  confidence: number
}

interface ExtractionResult {
  entities: Entity[]
  total: number
}

export default function ExtractPage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleExtract = async () => {
    if (!text.trim()) {
      toast.error('Введите текст для извлечения данных')
      return
    }

    try {
      setLoading(true)
      const data = await api.extractEntities(text.trim())
      setResult(data)
      toast.success('Извлечение выполнено')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to extract')
    } finally {
      setLoading(false)
    }
  }

  const groupedEntities = result?.entities.reduce((acc, entity) => {
    if (!acc[entity.type]) acc[entity.type] = []
    acc[entity.type].push(entity)
    return acc
  }, {} as Record<string, Entity[]>)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-primary-600" />
          Извлечение данных
        </h1>
        <p className="text-gray-600 mt-1">Автоматическое извлечение сущностей из текста (люди, места, организации и т.д.)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Исходный текст
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Вставьте текст для извлечения сущностей..."
            rows={15}
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
          <button
            onClick={handleExtract}
            disabled={loading || !text.trim()}
            className="mt-4 w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Извлечение...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Извлечь данные
              </>
            )}
          </button>
        </div>

        {/* Output */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Извлечённые сущности ({result?.total || 0})
          </label>
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 min-h-[400px] max-h-[500px] overflow-y-auto">
            {result && groupedEntities ? (
              <div className="space-y-4">
                {Object.entries(groupedEntities).map(([type, entities]) => (
                  <div key={type}>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 uppercase">
                      {type} ({entities.length})
                    </h3>
                    <div className="space-y-2">
                      {entities.map((entity, idx) => (
                        <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-gray-900">{entity.text}</span>
                            <span className="text-xs text-gray-500">
                              {(entity.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-400">
                  <Database className="w-12 h-12 mx-auto mb-3" />
                  <p>Извлечённые сущности появятся здесь</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
