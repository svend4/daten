/**
 * Admin Reindex Page
 */
import { useState } from 'react'
import { RefreshCw, Loader2, CheckCircle, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

export default function AdminReindexPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleReindex = async () => {
    if (!confirm('Вы уверены? Переиндексация может занять некоторое время.')) {
      return
    }

    try {
      setLoading(true)
      setResult(null)
      const data = await api.reindexDocuments()
      setResult(data)
      toast.success('Переиндексация завершена успешно')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to reindex')
      setResult({ error: true, message: err.response?.data?.detail || 'Ошибка переиндексации' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <RefreshCw className="w-8 h-8 text-primary-600" />
          Переиндексация
        </h1>
        <p className="text-gray-600 mt-1">Перестроение поискового индекса документов</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <RefreshCw className="w-16 h-16 text-primary-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Переиндексация документов
            </h2>
            <p className="text-gray-600">
              Эта операция перестроит поисковый индекс для всех документов в системе.
              Это может улучшить качество поиска и исправить проблемы с индексацией.
            </p>
          </div>

          {loading && (
            <div className="text-center py-8">
              <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
              <p className="text-gray-600">Выполняется переиндексация...</p>
              <p className="text-sm text-gray-500 mt-2">Это может занять несколько минут</p>
            </div>
          )}

          {result && !loading && (
            <div className={`rounded-lg p-6 mb-6 ${result.error ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'}`}>
              <div className="flex items-start gap-3">
                {result.error ? (
                  <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <h3 className={`font-semibold mb-1 ${result.error ? 'text-red-900' : 'text-green-900'}`}>
                    {result.error ? 'Ошибка' : 'Успешно'}
                  </h3>
                  <p className={result.error ? 'text-red-700' : 'text-green-700'}>
                    {result.message || 'Переиндексация завершена'}
                  </p>
                  {result.indexed_count !== undefined && (
                    <p className="text-sm mt-2 text-green-600">
                      Проиндексировано документов: {result.indexed_count}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          <button
            onClick={handleReindex}
            disabled={loading}
            className="w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Переиндексация...
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                Начать переиндексацию
              </>
            )}
          </button>

          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <strong>Внимание:</strong> Во время переиндексации поиск может работать некорректно.
              Рекомендуется выполнять эту операцию в период низкой активности пользователей.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
