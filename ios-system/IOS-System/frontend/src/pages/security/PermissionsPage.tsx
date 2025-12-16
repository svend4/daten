/**
 * PermissionsPage - Manage user roles and permissions
 */
import { useState } from 'react'
import { Shield, Users, Lock, Edit, Check, X } from 'lucide-react'
import { toast } from 'sonner'

interface Role {
  id: string
  name: string
  description: string
  userCount: number
  permissions: string[]
}

interface Permission {
  id: string
  name: string
  description: string
  category: string
}

export default function PermissionsPage() {
  const allPermissions: Permission[] = [
    // Documents
    { id: 'doc_read', name: 'Чтение документов', description: 'Просмотр всех документов', category: 'Документы' },
    { id: 'doc_create', name: 'Создание документов', description: 'Создание новых документов', category: 'Документы' },
    { id: 'doc_edit', name: 'Редактирование документов', description: 'Изменение существующих документов', category: 'Документы' },
    { id: 'doc_delete', name: 'Удаление документов', description: 'Удаление документов', category: 'Документы' },
    { id: 'doc_export', name: 'Экспорт документов', description: 'Экспорт данных в файлы', category: 'Документы' },

    // Search
    { id: 'search_basic', name: 'Базовый поиск', description: 'Использование обычного поиска', category: 'Поиск' },
    { id: 'search_semantic', name: 'Семантический поиск', description: 'Использование AI-поиска', category: 'Поиск' },
    { id: 'search_advanced', name: 'Расширенный поиск', description: 'Доступ к фильтрам и сложным запросам', category: 'Поиск' },

    // AI Features
    { id: 'ai_summarize', name: 'AI Резюме', description: 'Генерация резюме текста', category: 'AI Функции' },
    { id: 'ai_classify', name: 'AI Классификация', description: 'Классификация документов', category: 'AI Функции' },
    { id: 'ai_extract', name: 'AI Извлечение', description: 'Извлечение данных из текста', category: 'AI Функции' },
    { id: 'ai_chat', name: 'AI Чат', description: 'Использование AI ассистента', category: 'AI Функции' },

    // Admin
    { id: 'admin_users', name: 'Управление пользователями', description: 'Создание и редактирование пользователей', category: 'Администрирование' },
    { id: 'admin_roles', name: 'Управление ролями', description: 'Настройка ролей и прав доступа', category: 'Администрирование' },
    { id: 'admin_logs', name: 'Просмотр логов', description: 'Доступ к системным журналам', category: 'Администрирование' },
    { id: 'admin_settings', name: 'Системные настройки', description: 'Изменение настроек системы', category: 'Администрирование' },
    { id: 'admin_audit', name: 'Журнал аудита', description: 'Просмотр истории действий', category: 'Администрирование' },
  ]

  const [roles, setRoles] = useState<Role[]>([
    {
      id: '1',
      name: 'Администратор',
      description: 'Полный доступ ко всем функциям системы',
      userCount: 2,
      permissions: allPermissions.map(p => p.id)
    },
    {
      id: '2',
      name: 'Редактор',
      description: 'Создание и редактирование документов, использование AI',
      userCount: 15,
      permissions: [
        'doc_read', 'doc_create', 'doc_edit', 'doc_export',
        'search_basic', 'search_semantic', 'search_advanced',
        'ai_summarize', 'ai_classify', 'ai_extract', 'ai_chat'
      ]
    },
    {
      id: '3',
      name: 'Читатель',
      description: 'Только просмотр документов и базовый поиск',
      userCount: 45,
      permissions: ['doc_read', 'search_basic']
    },
    {
      id: '4',
      name: 'Гость',
      description: 'Минимальные права доступа',
      userCount: 8,
      permissions: ['doc_read']
    }
  ])

  const [editingRole, setEditingRole] = useState<string | null>(null)
  const [editedPermissions, setEditedPermissions] = useState<string[]>([])

  const handleEditRole = (roleId: string) => {
    const role = roles.find(r => r.id === roleId)
    if (role) {
      setEditingRole(roleId)
      setEditedPermissions([...role.permissions])
    }
  }

  const handleTogglePermission = (permissionId: string) => {
    if (editedPermissions.includes(permissionId)) {
      setEditedPermissions(editedPermissions.filter(p => p !== permissionId))
    } else {
      setEditedPermissions([...editedPermissions, permissionId])
    }
  }

  const handleSaveRole = () => {
    if (!editingRole) return

    setRoles(roles.map(role =>
      role.id === editingRole
        ? { ...role, permissions: editedPermissions }
        : role
    ))

    setEditingRole(null)
    setEditedPermissions([])
    toast.success('Права доступа обновлены')
  }

  const handleCancelEdit = () => {
    setEditingRole(null)
    setEditedPermissions([])
  }

  const groupedPermissions = allPermissions.reduce((acc, permission) => {
    if (!acc[permission.category]) {
      acc[permission.category] = []
    }
    acc[permission.category].push(permission)
    return acc
  }, {} as Record<string, Permission[]>)

  const getRoleColor = (roleName: string) => {
    switch (roleName) {
      case 'Администратор':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'Редактор':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'Читатель':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Роли и права доступа</h1>
        <p className="text-gray-600 mt-1">Управление ролями пользователей и их правами в системе</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего ролей</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{roles.length}</div>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего пользователей</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {roles.reduce((sum, role) => sum + role.userCount, 0)}
              </div>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600">Всего прав</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">{allPermissions.length}</div>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Lock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Roles List */}
      <div className="space-y-4">
        {roles.map((role) => (
          <div key={role.id} className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{role.name}</h3>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getRoleColor(role.name)}`}>
                    {role.userCount} {role.userCount === 1 ? 'пользователь' : 'пользователей'}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{role.description}</p>
              </div>

              {editingRole !== role.id && (
                <button
                  onClick={() => handleEditRole(role.id)}
                  className="flex items-center gap-2 px-4 py-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Редактировать
                </button>
              )}
            </div>

            {editingRole === role.id ? (
              <div className="space-y-4">
                {/* Permission Categories */}
                {Object.entries(groupedPermissions).map(([category, permissions]) => (
                  <div key={category}>
                    <h4 className="font-medium text-gray-900 mb-3">{category}</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {permissions.map((permission) => (
                        <label
                          key={permission.id}
                          className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={editedPermissions.includes(permission.id)}
                            onChange={() => handleTogglePermission(permission.id)}
                            className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                          />
                          <div className="flex-1">
                            <div className="font-medium text-sm text-gray-900">{permission.name}</div>
                            <div className="text-xs text-gray-600 mt-0.5">{permission.description}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Action Buttons */}
                <div className="flex items-center gap-2 pt-4 border-t border-gray-200">
                  <button
                    onClick={handleSaveRole}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <Check className="w-4 h-4" />
                    Сохранить
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  >
                    <X className="w-4 h-4" />
                    Отменить
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">
                    Права доступа ({role.permissions.length}/{allPermissions.length})
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {role.permissions.slice(0, 8).map((permId) => {
                    const perm = allPermissions.find(p => p.id === permId)
                    return perm ? (
                      <span
                        key={permId}
                        className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                      >
                        {perm.name}
                      </span>
                    ) : null
                  })}
                  {role.permissions.length > 8 && (
                    <span className="px-3 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">
                      +{role.permissions.length - 8} ещё
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <Lock className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Управление правами доступа</p>
            <p>
              Изменения прав доступа применяются немедленно ко всем пользователям с соответствующей ролью.
              Убедитесь, что вы не ограничиваете критически важные права для активных пользователей.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
