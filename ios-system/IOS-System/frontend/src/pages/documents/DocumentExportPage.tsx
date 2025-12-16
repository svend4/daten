/**
 * Document Export Page - Export documents to various formats
 */
import { useState } from 'react'
import { Download, FileJson, FileSpreadsheet, FileText, Loader2, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

type ExportFormat = 'json' | 'csv' | 'txt'

export default function DocumentExportPage() {
  const [exporting, setExporting] = useState(false)
  const [format, setFormat] = useState<ExportFormat>('json')
  const [includeMetadata, setIncludeMetadata] = useState(true)
  const [category, setCategory] = useState('')
  const [exportComplete, setExportComplete] = useState(false)

  const handleExport = async () => {
    try {
      setExporting(true)
      setExportComplete(false)

      // Fetch all documents (with optional category filter)
      const params: any = { limit: 1000 }
      if (category) params.category = category

      const data = await api.getDocuments(params)
      const documents = data.items || data || []

      if (documents.length === 0) {
        toast.error('Нет документов для экспорта')
        return
      }

      // Export based on format
      let content = ''
      let filename = ''
      let mimeType = ''

      if (format === 'json') {
        const exportData = documents.map((doc: any) => {
          if (!includeMetadata) {
            return {
              title: doc.title,
              content: doc.content
            }
          }
          return doc
        })
        content = JSON.stringify(exportData, null, 2)
        filename = `documents_export_${Date.now()}.json`
        mimeType = 'application/json'
      } else if (format === 'csv') {
        // CSV Header
        const headers = includeMetadata
          ? ['title', 'content', 'category', 'tags', 'created_at']
          : ['title', 'content']
        content = headers.join(',') + '\n'

        // CSV Rows
        documents.forEach((doc: any) => {
          const row = headers.map(header => {
            let value = doc[header] || ''
            if (header === 'tags' && Array.isArray(value)) {
              value = value.join(';')
            }
            // Escape quotes and wrap in quotes if contains comma
            value = String(value).replace(/"/g, '""')
            if (value.includes(',') || value.includes('\n')) {
              value = `"${value}"`
            }
            return value
          })
          content += row.join(',') + '\n'
        })
        filename = `documents_export_${Date.now()}.csv`
        mimeType = 'text/csv'
      } else if (format === 'txt') {
        documents.forEach((doc: any, index: number) => {
          content += `${'='.repeat(80)}\n`
          content += `Document ${index + 1}: ${doc.title}\n`
          if (includeMetadata) {
            content += `Category: ${doc.category || 'N/A'}\n`
            content += `Tags: ${Array.isArray(doc.tags) ? doc.tags.join(', ') : 'N/A'}\n`
            content += `Created: ${doc.created_at || 'N/A'}\n`
          }
          content += `${'='.repeat(80)}\n\n`
          content += doc.content + '\n\n'
        })
        filename = `documents_export_${Date.now()}.txt`
        mimeType = 'text/plain'
      }

      // Download file
      const blob = new Blob([content], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)

      setExportComplete(true)
      toast.success(`Экспортировано ${documents.length} документов`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ошибка экспорта')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Download className="w-8 h-8 text-primary-600" />
          Экспорт документов
        </h1>
        <p className="text-gray-600 mt-1">Экспортируйте документы в различных форматах</p>
      </div>

      {/* Format Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Выберите формат</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setFormat('json')}
            className={`p-6 rounded-lg border-2 transition-all ${
              format === 'json'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-primary-300'
            }`}
          >
            <FileJson className={`w-12 h-12 mx-auto mb-3 ${format === 'json' ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="font-semibold text-gray-900 mb-1">JSON</h3>
            <p className="text-sm text-gray-600">Структурированный формат для импорта</p>
          </button>

          <button
            onClick={() => setFormat('csv')}
            className={`p-6 rounded-lg border-2 transition-all ${
              format === 'csv'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-primary-300'
            }`}
          >
            <FileSpreadsheet className={`w-12 h-12 mx-auto mb-3 ${format === 'csv' ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="font-semibold text-gray-900 mb-1">CSV</h3>
            <p className="text-sm text-gray-600">Открывается в Excel, Google Sheets</p>
          </button>

          <button
            onClick={() => setFormat('txt')}
            className={`p-6 rounded-lg border-2 transition-all ${
              format === 'txt'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-primary-300'
            }`}
          >
            <FileText className={`w-12 h-12 mx-auto mb-3 ${format === 'txt' ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="font-semibold text-gray-900 mb-1">TXT</h3>
            <p className="text-sm text-gray-600">Простой текстовый формат</p>
          </button>
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Параметры экспорта</h2>

        <div className="space-y-4">
          {/* Metadata Toggle */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={includeMetadata}
              onChange={(e) => setIncludeMetadata(e.target.checked)}
              className="w-5 h-5 text-primary-600 rounded focus:ring-primary-500"
            />
            <div>
              <div className="font-medium text-gray-900">Включить метаданные</div>
              <div className="text-sm text-gray-600">
                Категория, теги, дата создания и другая информация
              </div>
            </div>
          </label>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Фильтр по категории (опционально)
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="Введите категорию для фильтрации"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-500 mt-1">
              Оставьте пустым для экспорта всех документов
            </p>
          </div>
        </div>
      </div>

      {/* Export Button */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <button
          onClick={handleExport}
          disabled={exporting}
          className="w-full px-6 py-4 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-lg font-semibold transition-colors"
        >
          {exporting ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Экспорт...
            </>
          ) : exportComplete ? (
            <>
              <CheckCircle className="w-6 h-6" />
              Экспорт завершён
            </>
          ) : (
            <>
              <Download className="w-6 h-6" />
              Экспортировать в {format.toUpperCase()}
            </>
          )}
        </button>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">ℹ️ Информация</h3>
        <ul className="text-blue-800 space-y-1 text-sm">
          <li>• JSON - лучший формат для последующего импорта</li>
          <li>• CSV - удобен для редактирования в таблицах</li>
          <li>• TXT - простой формат для чтения</li>
          <li>• Максимум 1000 документов за раз</li>
          <li>• Файл автоматически скачается после экспорта</li>
        </ul>
      </div>
    </div>
  )
}
