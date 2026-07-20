import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import Customers from './pages/Customers'
import Transactions from './pages/Transactions'
import Alerts from './pages/Alerts'

const queryClient = new QueryClient()

type Page = 'dashboard' | 'customers' | 'transactions' | 'alerts'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')

  const pages: { id: Page; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'customers', label: 'Customers' },
    { id: 'transactions', label: 'Transactions' },
    { id: 'alerts', label: 'Alerts' },
  ]

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AML</span>
              </div>
              <span className="text-white font-semibold text-lg">Risk Scoring System</span>
            </div>
            <div className="flex gap-6 text-sm">
              {pages.map(p => (
                <button
                  key={p.id}
                  onClick={() => setCurrentPage(p.id)}
                  className={`transition-colors ${
                    currentPage === p.id
                      ? 'text-white font-medium'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'customers' && <Customers />}
          {currentPage === 'transactions' && <Transactions />}
          {currentPage === 'alerts' && <Alerts />}
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App