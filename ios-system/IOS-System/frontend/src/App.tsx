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
import SemanticSearchPage from '@pages/SemanticSearchPage'

// Graph Pages
import KnowledgeGraphPage from '@pages/graph/KnowledgeGraphPage'
import EntitiesPage from '@pages/graph/EntitiesPage'
import RelationsPage from '@pages/graph/RelationsPage'

// AI Pages
import SummarizePage from '@pages/ai/SummarizePage'

// Admin Pages
import AdminStatsPage from '@pages/admin/AdminStatsPage'
import AdminServicesPage from '@pages/admin/AdminServicesPage'

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
                    <Route path="/documents/new" element={<div className="p-6">Создание документа (Coming Soon)</div>} />
                    <Route path="/search" element={<div className="p-6">Поиск документов (Coming Soon)</div>} />
                    <Route path="/search/semantic" element={<SemanticSearchPage />} />

                    {/* Knowledge Graph */}
                    <Route path="/graph" element={<KnowledgeGraphPage />} />
                    <Route path="/graph/entities" element={<EntitiesPage />} />
                    <Route path="/graph/relations" element={<RelationsPage />} />

                    {/* AI Features */}
                    <Route path="/ai/summarize" element={<SummarizePage />} />
                    <Route path="/ai/classify" element={<div className="p-6">Классификация текста (Coming Soon)</div>} />
                    <Route path="/ai/extract" element={<div className="p-6">Извлечение данных (Coming Soon)</div>} />
                    <Route path="/ai/chat" element={<div className="p-6">AI Чат (Coming Soon)</div>} />

                    {/* Admin */}
                    <Route path="/admin/stats" element={<AdminStatsPage />} />
                    <Route path="/admin/services" element={<AdminServicesPage />} />
                    <Route path="/admin/logs" element={<div className="p-6">Системные логи (Coming Soon)</div>} />
                    <Route path="/admin/reindex" element={<div className="p-6">Переиндексация (Coming Soon)</div>} />

                    {/* Settings */}
                    <Route path="/settings" element={<div className="p-6">Настройки (Coming Soon)</div>} />

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
