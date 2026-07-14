import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, Database, GitBranch, BarChart3 } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Datasets from './pages/Datasets';
import Pipelines from './pages/Pipelines';
import Analytics from './pages/Analytics';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-900">
        <nav className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <span className="text-xl font-bold text-white">AI-Native Data App</span>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/" className="flex items-center px-3 py-2 text-gray-300 hover:text-white">
                  <LayoutDashboard className="w-5 h-5 mr-2" />
                  Dashboard
                </Link>
                <Link to="/datasets" className="flex items-center px-3 py-2 text-gray-300 hover:text-white">
                  <Database className="w-5 h-5 mr-2" />
                  Datasets
                </Link>
                <Link to="/pipelines" className="flex items-center px-3 py-2 text-gray-300 hover:text-white">
                  <GitBranch className="w-5 h-5 mr-2" />
                  Pipelines
                </Link>
                <Link to="/analytics" className="flex items-center px-3 py-2 text-gray-300 hover:text-white">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Analytics
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/pipelines" element={<Pipelines />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
