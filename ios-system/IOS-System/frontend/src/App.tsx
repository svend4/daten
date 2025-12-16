/**
 * App.tsx - Main application component with routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { useEffect } from 'react'

// Store
import { useAuthStore } from '@store/authStore'

// Pages
import LoginPage from '@pages/LoginPage'
import DashboardPage from '@pages/DashboardPage'
import DocumentsPage from '@pages/DocumentsPage'
import DocumentNewPage from '@pages/DocumentNewPage'
import SearchPage from '@pages/SearchPage'
import SemanticSearchPage from '@pages/SemanticSearchPage'
import SettingsPage from '@pages/SettingsPage'

// Graph Pages
import KnowledgeGraphPage from '@pages/graph/KnowledgeGraphPage'
import EntitiesPage from '@pages/graph/EntitiesPage'
import RelationsPage from '@pages/graph/RelationsPage'

// AI Pages
import SummarizePage from '@pages/ai/SummarizePage'
import ClassifyPage from '@pages/ai/ClassifyPage'
import ExtractPage from '@pages/ai/ExtractPage'
import ChatPage from '@pages/ai/ChatPage'

// Admin Pages
import AdminStatsPage from '@pages/admin/AdminStatsPage'
import AdminServicesPage from '@pages/admin/AdminServicesPage'
import AdminLogsPage from '@pages/admin/AdminLogsPage'
import AdminReindexPage from '@pages/admin/AdminReindexPage'

// Layout
import Layout from './components/Layout'

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  const { fetchUser, isAuthenticated } = useAuthStore()

  // Fetch user on mount
  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={!isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" />} 
          />

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              isAuthenticated ? (
                <Layout>
                  <Routes>
                    {/* Dashboard */}
                    <Route path="/dashboard" element={<DashboardPage />} />

                    {/* Documents */}
                    <Route path="/documents" element={<DocumentsPage />} />
                    <Route path="/documents/new" element={<DocumentNewPage />} />
                    <Route path="/search" element={<SearchPage />} />
                    <Route path="/search/semantic" element={<SemanticSearchPage />} />

                    {/* Knowledge Graph */}
                    <Route path="/graph" element={<KnowledgeGraphPage />} />
                    <Route path="/graph/entities" element={<EntitiesPage />} />
                    <Route path="/graph/relations" element={<RelationsPage />} />

                    {/* AI Features */}
                    <Route path="/ai/summarize" element={<SummarizePage />} />
                    <Route path="/ai/classify" element={<ClassifyPage />} />
                    <Route path="/ai/extract" element={<ExtractPage />} />
                    <Route path="/ai/chat" element={<ChatPage />} />

                    {/* Admin */}
                    <Route path="/admin/stats" element={<AdminStatsPage />} />
                    <Route path="/admin/services" element={<AdminServicesPage />} />
                    <Route path="/admin/logs" element={<AdminLogsPage />} />
                    <Route path="/admin/reindex" element={<AdminReindexPage />} />

                    {/* Settings */}
                    <Route path="/settings" element={<SettingsPage />} />

                    {/* Default & 404 */}
                    <Route path="/" element={<Navigate to="/dashboard" />} />
                    <Route path="*" element={<div className="p-6">404 - Страница не найдена</div>} />
                  </Routes>
                </Layout>
              ) : (
                <Navigate to="/login" />
              )
            }
          />
        </Routes>
      </BrowserRouter>

      {/* Toast notifications */}
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  )
}

export default App
