/**
 * AI Text Classification Page
 */
import { useState } from 'react'
import { Brain, Loader2, FileText } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface ClassificationResult {
  category: string
  confidence: number
  subcategories?: string[]
}

export default function ClassifyPage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<ClassificationResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleClassify = async () => {
    if (!text.trim()) {
      toast.error('Введите текст для классификации')
      return
    }

    try {
      setLoading(true)
      const data = await api.classifyText(text.trim())
      setResult(data)
      toast.success('Классификация выполнена')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to classify')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="w-8 h-8 text-primary-600" />
          Классификация текста
        </h1>
        <p className="text-gray-600 mt-1">Автоматическое определение категории и тематики текста</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Текст для классификации
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Вставьте текст для классификации..."
            rows={15}
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
          <button
            onClick={handleClassify}
            disabled={loading || !text.trim()}
            className="mt-4 w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Классификация...
              </>
            ) : (
              <>
                <Brain className="w-5 h-5" />
                Классифицировать
              </>
            )}
          </button>
        </div>

        {/* Output */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Результат классификации
          </label>
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 min-h-[400px]">
            {result ? (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-600 mb-2">Категория:</div>
                  <div className="text-2xl font-bold text-primary-700">{result.category}</div>
                </div>

                <div>
                  <div className="text-sm text-gray-600 mb-2">Уверенность:</div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-primary-600 h-4 rounded-full transition-all"
                        style={{ width: `${(result.confidence * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <div className="text-lg font-semibold text-gray-900">
                      {(result.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {result.subcategories && result.subcategories.length > 0 && (
                  <div>
                    <div className="text-sm text-gray-600 mb-2">Подкатегории:</div>
                    <div className="flex flex-wrap gap-2">
                      {result.subcategories.map((sub, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                        >
                          {sub}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-400">
                  <FileText className="w-12 h-12 mx-auto mb-3" />
                  <p>Результат появится здесь после классификации</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
