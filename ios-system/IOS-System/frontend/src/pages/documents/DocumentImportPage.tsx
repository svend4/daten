/**
 * Document Bulk Import Page - Import documents from JSON/CSV
 */
import { useState } from 'react'
import { Download, Upload, Loader2, CheckCircle, AlertCircle, FileJson, FileSpreadsheet } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface ImportResult {
  success: number
  failed: number
  total: number
  errors: string[]
}

export default function DocumentImportPage() {
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [fileType, setFileType] = useState<'json' | 'csv'>('json')

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      setImporting(true)
      setResult(null)

      const text = await file.text()
      let documents: any[] = []

      if (fileType === 'json') {
        const data = JSON.parse(text)
        documents = Array.isArray(data) ? data : [data]
      } else if (fileType === 'csv') {
        documents = parseCSV(text)
      }

      // Import documents
      const results = await importDocuments(documents)
      setResult(results)

      if (results.success > 0) {
        toast.success(`Импортировано ${results.success} из ${results.total} документов`)
      } else {
        toast.error('Не удалось импортировать документы')
      }
    } catch (error: any) {
      toast.error(error.message || 'Ошибка импорта')
      setResult({
        success: 0,
        failed: 0,
        total: 0,
        errors: [error.message || 'Ошибка импорта']
      })
    } finally {
      setImporting(false)
    }
  }

  const parseCSV = (text: string): any[] => {
    const lines = text.split('\n').filter(line => line.trim())
    if (lines.length < 2) return []

    const headers = lines[0].split(',').map(h => h.trim())
    const documents = []

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim())
      const doc: any = {}
      headers.forEach((header, index) => {
        doc[header] = values[index] || ''
      })
      documents.push(doc)
    }

    return documents
  }

  const importDocuments = async (documents: any[]): Promise<ImportResult> => {
    const result: ImportResult = {
      success: 0,
      failed: 0,
      total: documents.length,
      errors: []
    }

    for (const doc of documents) {
      try {
        // Validate required fields
        if (!doc.title || !doc.content) {
          result.failed++
          result.errors.push(`Document missing title or content: ${JSON.stringify(doc)}`)
          continue
        }

        // Create document
        await api.createDocument({
          title: doc.title,
          content: doc.content,
          category: doc.category,
          tags: typeof doc.tags === 'string' ? doc.tags.split(',').map((t: string) => t.trim()) : doc.tags
        })

        result.success++
      } catch (error: any) {
        result.failed++
        result.errors.push(`Failed to import "${doc.title}": ${error.response?.data?.detail || error.message}`)
      }
    }

    return result
  }

  const downloadTemplate = (type: 'json' | 'csv') => {
    let content = ''
    let filename = ''
    let mimeType = ''

    if (type === 'json') {
      const template = [
        {
          title: 'Пример документа 1',
          content: 'Содержимое первого документа',
          category: 'example',
          tags: ['пример', 'шаблон']
        },
        {
          title: 'Пример документа 2',
          content: 'Содержимое второго документа',
          category: 'example',
          tags: ['пример']
        }
      ]
      content = JSON.stringify(template, null, 2)
      filename = 'template.json'
      mimeType = 'application/json'
    } else {
      content = 'title,content,category,tags\n'
      content += 'Пример документа 1,Содержимое первого документа,example,"пример,шаблон"\n'
      content += 'Пример документа 2,Содержимое второго документа,example,пример'
      filename = 'template.csv'
      mimeType = 'text/csv'
    }

    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    toast.success(`Шаблон ${type.toUpperCase()} скачан`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Download className="w-8 h-8 text-primary-600" />
          Массовый импорт
        </h1>
        <p className="text-gray-600 mt-1">Импорт документов из JSON или CSV файлов</p>
      </div>

      {/* Format Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Выберите формат</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => setFileType('json')}
            className={`p-6 rounded-lg border-2 transition-all ${
              fileType === 'json'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-primary-300'
            }`}
          >
            <FileJson className={`w-12 h-12 mx-auto mb-3 ${fileType === 'json' ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="font-semibold text-gray-900 mb-1">JSON</h3>
            <p className="text-sm text-gray-600">Структурированный формат с поддержкой вложенных данных</p>
          </button>

          <button
            onClick={() => setFileType('csv')}
            className={`p-6 rounded-lg border-2 transition-all ${
              fileType === 'csv'
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-200 hover:border-primary-300'
            }`}
          >
            <FileSpreadsheet className={`w-12 h-12 mx-auto mb-3 ${fileType === 'csv' ? 'text-primary-600' : 'text-gray-400'}`} />
            <h3 className="font-semibold text-gray-900 mb-1">CSV</h3>
            <p className="text-sm text-gray-600">Табличный формат, совместимый с Excel</p>
          </button>
        </div>
      </div>

      {/* Template Download */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">📝 Скачайте шаблон</h3>
        <p className="text-blue-800 mb-4">
          Используйте шаблон для правильного форматирования данных
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => downloadTemplate('json')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Шаблон JSON
          </button>
          <button
            onClick={() => downloadTemplate('csv')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Шаблон CSV
          </button>
        </div>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Загрузите файл</h2>
        <label className="block">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-primary-400 transition-colors cursor-pointer">
            <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Выберите {fileType.toUpperCase()} файл
            </h3>
            <p className="text-gray-600">Нажмите для выбора или перетащите файл сюда</p>
          </div>
          <input
            type="file"
            accept={fileType === 'json' ? '.json' : '.csv'}
            onChange={handleFileUpload}
            disabled={importing}
            className="hidden"
          />
        </label>
      </div>

      {/* Loading */}
      {importing && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 text-primary-600 animate-spin" />
          <p className="text-gray-600">Импорт документов...</p>
        </div>
      )}

      {/* Results */}
      {result && !importing && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Результаты импорта</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Всего</div>
              <div className="text-2xl font-bold text-gray-900">{result.total}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-green-600 mb-1 flex items-center gap-1">
                <CheckCircle className="w-4 h-4" />
                Успешно
              </div>
              <div className="text-2xl font-bold text-green-900">{result.success}</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <div className="text-sm text-red-600 mb-1 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                Ошибки
              </div>
              <div className="text-2xl font-bold text-red-900">{result.failed}</div>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div>
              <h3 className="font-semibold text-red-900 mb-2">Ошибки:</h3>
              <div className="bg-red-50 rounded-lg p-4 max-h-64 overflow-y-auto">
                {result.errors.map((error, index) => (
                  <div key={index} className="text-sm text-red-800 mb-1">
                    • {error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
