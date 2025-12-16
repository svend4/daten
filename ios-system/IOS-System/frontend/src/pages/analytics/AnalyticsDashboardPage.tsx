/**
 * Analytics Dashboard - Overview with charts
 */
import { BarChart3, TrendingUp, FileText, Users, Activity } from 'lucide-react'

export default function AnalyticsDashboardPage() {
  const stats = [
    { label: 'Всего документов', value: '1,234', change: '+12%', icon: FileText, color: 'blue' },
    { label: 'Активных пользователей', value: '89', change: '+5%', icon: Users, color: 'green' },
    { label: 'Поисков за месяц', value: '3,456', change: '+23%', icon: Activity, color: 'purple' },
    { label: 'Новых за неделю', value: '45', change: '+8%', icon: TrendingUp, color: 'orange' }
  ]

  const recentActivity = [
    { action: 'Создан документ', user: 'admin', time: '5 мин назад' },
    { action: 'Поиск выполнен', user: 'demo', time: '15 мин назад' },
    { action: 'Документ обновлён', user: 'admin', time: '1 час назад' }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-8 h-8 text-primary-600" />
          Аналитика
        </h1>
        <p className="text-gray-600 mt-1">Статистика и метрики системы</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-2">
              <stat.icon className={`w-8 h-8 text-${stat.color}-600`} />
              <span className={`text-sm font-medium text-${stat.color}-600`}>{stat.change}</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-sm text-gray-600">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Placeholder */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Документы по месяцам</h2>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-gray-500">График: Линейный график</div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Категории документов</h2>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-gray-500">График: Круговая диаграмма</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Последняя активность</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentActivity.map((item, idx) => (
            <div key={idx} className="px-6 py-4 flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">{item.action}</div>
                <div className="text-sm text-gray-600">Пользователь: {item.user}</div>
              </div>
              <div className="text-sm text-gray-500">{item.time}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
