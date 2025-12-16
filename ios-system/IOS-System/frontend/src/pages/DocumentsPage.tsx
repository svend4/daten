/**
 * Documents Page - Document management
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  FileText,
  Search,
  Plus,
  Edit,
  Trash2,
  Eye
} from 'lucide-react'
import api from '@services/api'
import { Link } from 'react-router-dom'

interface Document {
  id: string
  title: string
  content: string
  category: string
  status: string
  createdAt: string
  updatedAt: string
  viewCount: number
}

export default function DocumentsPage() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [page, setPage] = useState(1)

  // Fetch documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents', page, search, category],
    queryFn: () => api.getDocuments({
      page,
      limit: 20,
      search: search || undefined,
      category: category || undefined,
    }),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Documents</h1>
          <p className="mt-2 text-gray-600">
            Manage and organize your documents
          </p>
        </div>
        <Link
          to="/documents/new"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Document
        </Link>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Category filter */}
          <div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              <option value="report">Report</option>
              <option value="memo">Memo</option>
              <option value="note">Note</option>
              <option value="proposal">Proposal</option>
              <option value="contract">Contract</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="p-8">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gray-200 rounded" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-3/4" />
                    <div className="h-3 bg-gray-200 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <div className="divide-y divide-gray-200">
              {data.items.map((doc: Document) => (
                <DocumentRow key={doc.id} document={doc} />
              ))}
            </div>

            {/* Pagination */}
            {data.total > 20 && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, data.total)} of {data.total} documents
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                      className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage(page + 1)}
                      disabled={!data.hasMore}
                      className="px-3 py-1 border border-gray-300 rounded-lg disabled:opacity-50 hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new document.
            </p>
            <div className="mt-6">
              <Link
                to="/documents/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Document
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Document Row Component
interface DocumentRowProps {
  document: Document
}

function DocumentRow({ document }: DocumentRowProps) {
  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary-600" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <Link to={`/documents/${document.id}`} className="block">
              <h3 className="text-sm font-medium text-gray-900 truncate hover:text-primary-600">
                {document.title}
              </h3>
              <div className="mt-1 flex items-center space-x-3 text-xs text-gray-500">
                <span className="capitalize">{document.category}</span>
                <span>•</span>
                <span>{new Date(document.createdAt).toLocaleDateString()}</span>
                <span>•</span>
                <span className="flex items-center">
                  <Eye className="w-3 h-3 mr-1" />
                  {document.viewCount} views
                </span>
              </div>
            </Link>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          <Link
            to={`/documents/${document.id}`}
            className="p-2 text-gray-400 hover:text-primary-600 rounded-lg hover:bg-primary-50"
            title="View"
          >
            <Eye className="w-4 h-4" />
          </Link>
          <Link
            to={`/documents/${document.id}/edit`}
            className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50"
            title="Edit"
          >
            <Edit className="w-4 h-4" />
          </Link>
          <button
            className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
