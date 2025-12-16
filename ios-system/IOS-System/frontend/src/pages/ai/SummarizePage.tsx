/**
 * AI Text Summarization Page
 */
import { useState } from 'react'
import { FileText, Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@services/api'

export default function SummarizePage() {
  const [text, setText] = useState('')
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSummarize = async () => {
    if (!text.trim()) {
      toast.error('Введите текст для резюмирования')
      return
    }

    try {
      setLoading(true)
      const response = await apiClient.post('/ai/summarize', { text: text.trim() })
      setSummary(response.data.summary || 'Резюме не создано')
      toast.success('Резюме создано успешно')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to summarize')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-8 h-8 text-primary-600" />
          Резюме текста
        </h1>
        <p className="text-gray-600 mt-1">Автоматическое создание краткого резюме длинного текста</p>
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
            placeholder="Вставьте текст для резюмирования..."
            rows={15}
            className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
          <button
            onClick={handleSummarize}
            disabled={loading || !text.trim()}
            className="mt-4 w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Создание резюме...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Создать резюме
              </>
            )}
          </button>
        </div>

        {/* Output */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Резюме
          </label>
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 min-h-[400px]">
            {summary ? (
              <p className="text-gray-900 whitespace-pre-wrap">{summary}</p>
            ) : (
              <p className="text-gray-400 italic">Резюме появится здесь после обработки...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
