/**
 * Document Statistics Page
 */
import { FileText, BarChart2, PieChart } from 'lucide-react'

export default function DocumentStatsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="w-8 h-8 text-primary-600" />
          Статистика документов
        </h1>
        <p className="text-gray-600 mt-1">Детальная аналитика по документам</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <BarChart2 className="w-8 h-8 text-blue-600 mb-2" />
          <div className="text-2xl font-bold">1,234</div>
          <div className="text-gray-600">Всего документов</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <PieChart className="w-8 h-8 text-green-600 mb-2" />
          <div className="text-2xl font-bold">456</div>
          <div className="text-gray-600">С тегами</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <FileText className="w-8 h-8 text-purple-600 mb-2" />
          <div className="text-2xl font-bold">12.5 MB</div>
          <div className="text-gray-600">Общий размер</div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">Распределение по категориям</h2>
        {['work', 'personal', 'tutorial', 'reports'].map((cat) => (
          <div key={cat} className="mb-3">
            <div className="flex justify-between text-sm mb-1">
              <span>{cat}</span>
              <span>25%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-primary-600 h-2 rounded-full" style={{ width: '25%' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
