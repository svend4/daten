/**
 * Reports Export Page
 */
import { Download, FileText, Calendar } from 'lucide-react'
import { toast } from 'sonner'

export default function ReportsPage() {
  const reports = [
    { name: 'Ежемесячный отчёт', desc: 'Статистика за последний месяц', format: 'PDF' },
    { name: 'Отчёт по документам', desc: 'Все документы с метаданными', format: 'CSV' },
    { name: 'Активность пользователей', desc: 'Логи активности', format: 'JSON' },
    { name: 'Аналитика поиска', desc: 'Статистика поисковых запросов', format: 'XLSX' }
  ]

  const handleExport = (name: string) => {
    toast.success(`Отчёт "${name}" экспортирован`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-8 h-8 text-primary-600" />
          Отчёты
        </h1>
        <p className="text-gray-600 mt-1">Экспорт аналитических отчётов</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((report) => (
          <div key={report.name} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">{report.name}</h3>
                <p className="text-sm text-gray-600">{report.desc}</p>
              </div>
              <span className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded font-medium">
                {report.format}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-500 mb-4">
              <Calendar className="w-4 h-4" />
              Обновлён: сегодня
            </div>
            <button
              onClick={() => handleExport(report.name)}
              className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center justify-center gap-2"
            >
              <Download className="w-4 h-4" />
              Скачать отчёт
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
