/**
 * Activity Heatmap Page
 */
import { Activity } from 'lucide-react'

export default function ActivityHeatmapPage() {
  const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
  const hours = Array.from({ length: 24 }, (_, i) => i)

  const getActivityLevel = () => Math.floor(Math.random() * 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="w-8 h-8 text-primary-600" />
          Тепловая карта активности
        </h1>
        <p className="text-gray-600 mt-1">Активность пользователей по дням и часам</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="grid grid-cols-25 gap-1">
            <div className="col-span-1" />
            {hours.map(h => (
              <div key={h} className="text-xs text-center text-gray-600">{h}h</div>
            ))}
            {days.map(day => (
              <>
                <div key={day} className="text-sm font-medium text-gray-700 flex items-center">{day}</div>
                {hours.map(h => {
                  const level = getActivityLevel()
                  const colors = ['bg-gray-100', 'bg-green-200', 'bg-green-400', 'bg-green-600', 'bg-green-800']
                  return <div key={`${day}-${h}`} className={`h-8 rounded ${colors[level]}`} title={`${day} ${h}:00`} />
                })}
              </>
            ))}
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
          <span>Меньше</span>
          {[0,1,2,3,4].map(i => (
            <div key={i} className={`w-4 h-4 rounded ${['bg-gray-100', 'bg-green-200', 'bg-green-400', 'bg-green-600', 'bg-green-800'][i]}`} />
          ))}
          <span>Больше</span>
        </div>
      </div>
    </div>
  )
}
