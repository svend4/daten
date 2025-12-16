/**
 * Layout Component - Main application layout with sidebar and header
 */
import { ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@store/authStore'
import {
  LayoutDashboard,
  FileText,
  Search,
  Settings,
  LogOut,
  Menu,
  X,
  User,
  Bell,
  Network,
  Bot,
  Shield,
  ChevronDown,
  ChevronRight,
  Sparkles,
  GitBranch,
  Database,
  PenTool,
  Brain,
  MessageSquare,
  BarChart3,
  Activity,
  FileText as FileIcon,
  Server,
  RefreshCw,
  Upload,
  Download,
  History,
  Bookmark,
  Clock,
  SlidersHorizontal,
  Tag as TagIcon,
  TrendingUp,
} from 'lucide-react'
import clsx from 'clsx'

interface LayoutProps {
  children: ReactNode
}

interface NavigationItem {
  name: string
  href?: string
  icon: any
  children?: NavigationItem[]
}

const navigation: NavigationItem[] = [
  { name: 'Главная', href: '/dashboard', icon: LayoutDashboard },
  {
    name: 'Документы',
    icon: FileText,
    children: [
      { name: 'Все документы', href: '/documents', icon: FileIcon },
      { name: 'Создать документ', href: '/documents/new', icon: PenTool },
      { name: 'Загрузка файлов', href: '/documents/upload', icon: Upload },
      { name: 'Массовый импорт', href: '/documents/import', icon: Download },
      { name: 'Экспорт данных', href: '/documents/export', icon: Download },
      { name: 'История версий', href: '/documents/history', icon: History },
    ],
  },
  {
    name: 'Поиск',
    icon: Search,
    children: [
      { name: 'Быстрый поиск', href: '/search', icon: Search },
      { name: 'Семантический поиск', href: '/search/semantic', icon: Sparkles },
      { name: 'Расширенный поиск', href: '/search/advanced', icon: SlidersHorizontal },
      { name: 'Поиск по тегам', href: '/search/tags', icon: TagIcon },
      { name: 'Сохранённые поиски', href: '/search/saved', icon: Bookmark },
      { name: 'История поиска', href: '/search/history', icon: Clock },
    ],
  },
  {
    name: 'Граф знаний',
    icon: Network,
    children: [
      { name: 'Визуализация', href: '/graph', icon: GitBranch },
      { name: 'Сущности', href: '/graph/entities', icon: Database },
      { name: 'Связи', href: '/graph/relations', icon: Network },
    ],
  },
  {
    name: 'AI Функции',
    icon: Bot,
    children: [
      { name: 'Резюме текста', href: '/ai/summarize', icon: FileIcon },
      { name: 'Классификация', href: '/ai/classify', icon: Brain },
      { name: 'Извлечение данных', href: '/ai/extract', icon: Sparkles },
      { name: 'AI Чат', href: '/ai/chat', icon: MessageSquare },
    ],
  },
  {
    name: 'Аналитика',
    icon: BarChart3,
    children: [
      { name: 'Dashboard', href: '/analytics', icon: BarChart3 },
      { name: 'Статистика документов', href: '/analytics/documents', icon: FileIcon },
      { name: 'Карта активности', href: '/analytics/heatmap', icon: Activity },
      { name: 'Отчёты', href: '/analytics/reports', icon: Download },
      { name: 'Trending', href: '/analytics/trending', icon: TrendingUp },
    ],
  },
  {
    name: 'Администрирование',
    icon: Shield,
    children: [
      { name: 'Статистика', href: '/admin/stats', icon: BarChart3 },
      { name: 'Статус сервисов', href: '/admin/services', icon: Activity },
      { name: 'Системные логи', href: '/admin/logs', icon: Server },
      { name: 'Переиндексация', href: '/admin/reindex', icon: RefreshCw },
    ],
  },
  { name: 'Настройки', href: '/settings', icon: Settings },
]

// Navigation item component with collapse support
function NavItem({ item, onNavigate }: { item: NavigationItem; onNavigate?: () => void }) {
  const location = useLocation()
  const hasActiveChild = item.children?.some((child) => location.pathname === child.href)
  const [isOpen, setIsOpen] = useState(hasActiveChild || false)

  const hasChildren = item.children && item.children.length > 0
  const isActive = item.href ? location.pathname === item.href : false

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            setIsOpen(!isOpen)
          }}
          className={clsx(
            'w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors',
            hasActiveChild
              ? 'bg-primary-50 text-primary-700'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          )}
        >
          <div className="flex items-center">
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
          </div>
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        {isOpen && (
          <div className="ml-4 mt-1 space-y-1">
            {item.children?.map((child) => (
              <Link
                key={child.name}
                to={child.href!}
                onClick={onNavigate}
                className={clsx(
                  'flex items-center px-3 py-2 text-sm rounded-lg transition-colors',
                  location.pathname === child.href
                    ? 'bg-primary-100 text-primary-800'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <child.icon className="w-4 h-4 mr-3" />
                {child.name}
              </Link>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Link
      to={item.href!}
      onClick={onNavigate}
      className={clsx(
        'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
        isActive
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      )}
    >
      <item.icon className="w-5 h-5 mr-3" />
      {item.name}
    </Link>
  )
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="fixed inset-0 bg-gray-900/80" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
            <div className="flex h-full flex-col">
              {/* Logo */}
              <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
                <div className="flex items-center">
                  <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span className="ml-3 font-semibold text-gray-900">IOS System</span>
                </div>
                <button onClick={() => setSidebarOpen(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Navigation */}
              <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
                {navigation.map((item) => (
                  <NavItem key={item.name} item={item} onNavigate={() => setSidebarOpen(false)} />
                ))}
              </nav>

              {/* User section */}
              <div className="border-t border-gray-200 p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-primary-600" />
                    </div>
                  </div>
                  <div className="ml-3 flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user?.fullName || user?.username}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="mt-3 w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 bg-white border-r border-gray-200">
          {/* Logo */}
          <div className="flex h-16 items-center px-6 border-b border-gray-200">
            <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="ml-3 font-semibold text-gray-900">IOS System</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavItem key={item.name} item={item} />
            ))}
          </nav>

          {/* User section */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-primary-600" />
                </div>
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.fullName || user?.username}
                </p>
                <p className="text-xs text-gray-500 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <div className="sticky top-0 z-10 flex h-16 bg-white border-b border-gray-200">
          <button
            type="button"
            className="px-4 text-gray-500 focus:outline-none lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex flex-1 justify-end items-center px-4 sm:px-6 lg:px-8">
            {/* Notifications */}
            <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
              <Bell className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
