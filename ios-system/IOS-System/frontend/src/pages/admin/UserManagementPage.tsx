/**
 * UserManagementPage - User management interface
 */
import { useState } from 'react'
import { Plus, Edit, Trash2, Shield, Mail } from 'lucide-react'
import { toast } from 'sonner'

interface User {
  id: string
  username: string
  email: string
  fullName: string
  role: string
  status: 'active' | 'inactive' | 'suspended'
  createdAt: string
  lastLogin?: string
}

export default function UserManagementPage() {
  const [users] = useState<User[]>([
    { id: '1', username: 'admin', email: 'admin@example.com', fullName: 'Администратор', role: 'Администратор', status: 'active', createdAt: '2024-01-01', lastLogin: new Date().toISOString() },
    { id: '2', username: 'user123', email: 'user123@example.com', fullName: 'Иван Иванов', role: 'Редактор', status: 'active', createdAt: '2024-02-15', lastLogin: new Date(Date.now() - 1000 * 60 * 30).toISOString() },
    { id: '3', username: 'viewer', email: 'viewer@example.com', fullName: 'Мария Петрова', role: 'Читатель', status: 'active', createdAt: '2024-03-10' },
    { id: '4', username: 'guest', email: 'guest@example.com', fullName: 'Гость', role: 'Гость', status: 'suspended', createdAt: '2024-04-01' }
  ])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'inactive': return 'bg-gray-100 text-gray-800'
      case 'suspended': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const diff = Date.now() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    if (minutes < 60) return `${minutes} мин назад`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours} ч назад`
    return date.toLocaleDateString('ru-RU')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Управление пользователями</h1>
          <p className="text-gray-600 mt-1">Управление учётными записями</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          <Plus className="w-4 h-4" />
          Добавить
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Всего</div>
          <div className="text-2xl font-bold mt-1">{users.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Активных</div>
          <div className="text-2xl font-bold text-green-600 mt-1">{users.filter(u => u.status === 'active').length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Заблокированных</div>
          <div className="text-2xl font-bold text-red-600 mt-1">{users.filter(u => u.status === 'suspended').length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-600">Онлайн</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">2</div>
        </div>
      </div>

      <div className="bg-white rounded-lg border">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Пользователь</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Последний вход</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map(user => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900">{user.fullName}</div>
                      <div className="text-sm text-gray-600 flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        {user.email}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-1 text-sm">
                      <Shield className="w-4 h-4 text-gray-400" />
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(user.status)}`}>
                      {user.status === 'active' ? 'Активен' : user.status === 'suspended' ? 'Заблокирован' : 'Неактивен'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {user.lastLogin ? formatTime(user.lastLogin) : 'Никогда'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button className="p-1 text-blue-600 hover:bg-blue-50 rounded"><Edit className="w-4 h-4" /></button>
                      <button onClick={() => toast.success('Пользователь удалён')} className="p-1 text-red-600 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
