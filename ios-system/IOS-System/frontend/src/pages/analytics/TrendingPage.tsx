/**
 * Trending Documents Page
 */
import { TrendingUp, Eye, Heart, Share2 } from 'lucide-react'

export default function TrendingPage() {
  const trending = [
    { title: 'Welcome to IOS System', views: 245, likes: 18, shares: 5, trend: '+15%' },
    { title: 'How to Use Search', views: 189, likes: 12, shares: 3, trend: '+8%' },
    { title: 'Knowledge Graph Explained', views: 156, likes: 9, shares: 2, trend: '+12%' },
    { title: 'Getting Started Guide', views: 134, likes: 7, shares: 1, trend: '+5%' }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-8 h-8 text-primary-600" />
          Trending документы
        </h1>
        <p className="text-gray-600 mt-1">Самые популярные документы</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 divide-y">
        {trending.map((doc, idx) => (
          <div key={idx} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="text-2xl font-bold text-gray-400">#{idx + 1}</div>
                <div>
                  <h3 className="font-semibold text-gray-900">{doc.title}</h3>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <Eye className="w-4 h-4" /> {doc.views}
                    </span>
                    <span className="flex items-center gap-1">
                      <Heart className="w-4 h-4" /> {doc.likes}
                    </span>
                    <span className="flex items-center gap-1">
                      <Share2 className="w-4 h-4" /> {doc.shares}
                    </span>
                  </div>
                </div>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded font-medium">
                {doc.trend}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
