import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'

const queryClient = new QueryClient()

function App() {
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
            <div className="flex gap-6 text-sm text-gray-400">
              <span className="text-white font-medium">Dashboard</span>
              <span>Customers</span>
              <span>Transactions</span>
              <span>Alerts</span>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">
          <Dashboard />
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App