/**
 * Dashboard Page - Main landing page after login
 */
import { useQuery } from '@tanstack/react-query'
import { 
  FileText, 
  Search, 
  TrendingUp, 
  Users,
  Clock,
  Activity
} from 'lucide-react'
import api from '@services/api'

interface DashboardStats {
  totalDocuments: number
  recentSearches: number
  activeUsers: number
  documentsToday: number
}

interface RecentActivity {
  id: string
  type: string
  description: string
  timestamp: string
  user: string
}

export default function DashboardPage() {
  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => api.getDashboardStats(),
  })

  // Fetch recent activity
  const { data: activities, isLoading: activitiesLoading } = useQuery({
    queryKey: ['recentActivity'],
    queryFn: () => api.getRecentActivity(10),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back! Here's an overview of your IOS System.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Documents"
          value={stats?.totalDocuments || 0}
          icon={FileText}
          color="blue"
          loading={statsLoading}
        />
        <StatCard
          title="Searches Today"
          value={stats?.recentSearches || 0}
          icon={Search}
          color="green"
          loading={statsLoading}
        />
        <StatCard
          title="Active Users"
          value={stats?.activeUsers || 0}
          icon={Users}
          color="purple"
          loading={statsLoading}
        />
        <StatCard
          title="Documents Today"
          value={stats?.documentsToday || 0}
          icon={TrendingUp}
          color="orange"
          loading={statsLoading}
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <Activity className="w-5 h-5 text-gray-500 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">
              Recent Activity
            </h2>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {activitiesLoading ? (
            <div className="px-6 py-4">
              <div className="animate-pulse space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : activities && activities.length > 0 ? (
            activities.map((activity: RecentActivity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))
          ) : (
            <div className="px-6 py-8 text-center text-gray-500">
              No recent activity
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <QuickActionButton
            title="New Document"
            description="Create a new document"
            icon={FileText}
            onClick={() => window.location.href = '/documents/new'}
          />
          <QuickActionButton
            title="Search"
            description="Find documents quickly"
            icon={Search}
            onClick={() => window.location.href = '/search'}
          />
          <QuickActionButton
            title="Recent"
            description="View recent documents"
            icon={Clock}
            onClick={() => window.location.href = '/documents?filter=recent'}
          />
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
interface StatCardProps {
  title: string
  value: number
  icon: React.ElementType
  color: 'blue' | 'green' | 'purple' | 'orange'
  loading?: boolean
}

function StatCard({ title, value, icon: Icon, color, loading }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
        <div className="h-8 bg-gray-200 rounded w-1/3" />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">
            {value.toLocaleString()}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}

// Activity Item Component
interface ActivityItemProps {
  activity: RecentActivity
}

function ActivityItem({ activity }: ActivityItemProps) {
  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <Activity className="w-4 h-4 text-primary-600" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-900">{activity.description}</p>
          <p className="text-xs text-gray-500 mt-1">
            {activity.user} • {new Date(activity.timestamp).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  )
}

// Quick Action Button Component
interface QuickActionButtonProps {
  title: string
  description: string
  icon: React.ElementType
  onClick: () => void
}

function QuickActionButton({ title, description, icon: Icon, onClick }: QuickActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-start p-4 border border-gray-200 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition-all"
    >
      <div className="flex-shrink-0">
        <Icon className="w-6 h-6 text-primary-600" />
      </div>
      <div className="ml-3 text-left">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        <p className="text-xs text-gray-500 mt-1">{description}</p>
      </div>
    </button>
  )
}
