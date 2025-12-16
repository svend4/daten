/**
 * Document History Page - View document version history
 */
import { useState, useEffect } from 'react'
import { History, Clock, User, FileText, RefreshCw, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import api from '@services/api'

interface DocumentVersion {
  id: string
  document_id: string
  version: number
  title: string
  content: string
  changed_by: string
  changed_at: string
  changes: {
    field: string
    old_value: string
    new_value: string
  }[]
}

export default function DocumentHistoryPage() {
  const [loading, setLoading] = useState(true)
  const [documents, setDocuments] = useState<any[]>([])
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)
  const [history, setHistory] = useState<DocumentVersion[]>([])

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const data = await api.getDocuments({ limit: 100 })
      setDocuments(data.items || data || [])
    } catch (error: any) {
      toast.error('Не удалось загрузить документы')
    } finally {
      setLoading(false)
    }
  }

  const loadHistory = async (docId: string) => {
    try {
      setSelectedDoc(docId)
      // For demo, create mock history
      const doc = documents.find(d => d.id === docId)
      if (!doc) return

      const mockHistory: DocumentVersion[] = [
        {
          id: 'v3',
          document_id: docId,
          version: 3,
          title: doc.title,
          content: doc.content,
          changed_by: 'admin',
          changed_at: new Date().toISOString(),
          changes: [
            {
              field: 'content',
              old_value: 'Previous content...',
              new_value: doc.content
            }
          ]
        },
        {
          id: 'v2',
          document_id: docId,
          version: 2,
          title: doc.title,
          content: 'Previous version content...',
          changed_by: 'admin',
          changed_at: new Date(Date.now() - 86400000).toISOString(),
          changes: [
            {
              field: 'title',
              old_value: 'Old title',
              new_value: doc.title
            }
          ]
        },
        {
          id: 'v1',
          document_id: docId,
          version: 1,
          title: 'Initial version',
          content: 'Initial content...',
          changed_by: 'admin',
          changed_at: new Date(Date.now() - 172800000).toISOString(),
          changes: []
        }
      ]

      setHistory(mockHistory)
    } catch (error: any) {
      toast.error('Не удалось загрузить историю')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <History className="w-8 h-8 text-primary-600" />
          История версий
        </h1>
        <p className="text-gray-600 mt-1">Просмотр истории изменений документов</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Documents List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Документы</h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {documents.map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => loadHistory(doc.id)}
                  className={`w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors ${
                    selectedDoc === doc.id ? 'bg-primary-50 border-l-4 border-primary-600' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">{doc.title}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {formatDate(doc.updated_at || doc.created_at)}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Version History */}
        <div className="lg:col-span-2">
          {selectedDoc && history.length > 0 ? (
            <div className="bg-white rounded-lg border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="font-semibold text-gray-900">
                  История версий ({history.length})
                </h2>
              </div>

              <div className="p-6">
                {/* Timeline */}
                <div className="relative">
                  {history.map((version, index) => (
                    <div key={version.id} className="relative pb-8">
                      {/* Timeline line */}
                      {index < history.length - 1 && (
                        <div className="absolute left-4 top-10 bottom-0 w-0.5 bg-gray-200" />
                      )}

                      {/* Version card */}
                      <div className="relative flex gap-4">
                        {/* Version number badge */}
                        <div className="flex-shrink-0">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm ${
                            index === 0
                              ? 'bg-primary-600 text-white'
                              : 'bg-gray-200 text-gray-700'
                          }`}>
                            {version.version}
                          </div>
                        </div>

                        {/* Version details */}
                        <div className="flex-1 bg-gray-50 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h3 className="font-semibold text-gray-900 mb-1">
                                {version.title}
                              </h3>
                              <div className="flex items-center gap-4 text-sm text-gray-600">
                                <span className="flex items-center gap-1">
                                  <User className="w-4 h-4" />
                                  {version.changed_by}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Clock className="w-4 h-4" />
                                  {formatDate(version.changed_at)}
                                </span>
                              </div>
                            </div>
                            {index === 0 && (
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                                Текущая
                              </span>
                            )}
                          </div>

                          {/* Changes */}
                          {version.changes.length > 0 && (
                            <div className="mt-3 space-y-2">
                              <div className="text-sm font-medium text-gray-700">Изменения:</div>
                              {version.changes.map((change, changeIndex) => (
                                <div key={changeIndex} className="bg-white rounded p-3 text-sm">
                                  <div className="font-medium text-gray-700 mb-1">
                                    {change.field === 'title' ? 'Название' : 'Содержимое'}:
                                  </div>
                                  <div className="grid grid-cols-2 gap-2">
                                    <div>
                                      <div className="text-xs text-gray-500 mb-1">Было:</div>
                                      <div className="text-gray-600 line-clamp-2">
                                        {change.old_value}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-xs text-gray-500 mb-1">Стало:</div>
                                      <div className="text-gray-900 line-clamp-2">
                                        {change.new_value}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Content preview */}
                          <details className="mt-3">
                            <summary className="text-sm text-primary-600 cursor-pointer hover:text-primary-700">
                              Показать содержимое
                            </summary>
                            <div className="mt-2 p-3 bg-white rounded text-sm text-gray-700 max-h-40 overflow-y-auto">
                              {version.content}
                            </div>
                          </details>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : selectedDoc ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">История версий недоступна</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Выберите документ для просмотра истории</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
