import { useEffect, useState } from 'react';
import { Database, GitBranch, FileText, Activity, RefreshCw } from 'lucide-react';
import { getDatasets, getPipelines } from '../lib/db';

export default function Dashboard() {
  const [datasetCount, setDatasetCount] = useState(0);
  const [pipelineCount, setPipelineCount] = useState(0);
  const [totalRows, setTotalRows] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [datasets, pipelines] = await Promise.all([getDatasets(), getPipelines()]);
      setDatasetCount(datasets.length);
      setPipelineCount(pipelines.length);
      setTotalRows(datasets.reduce((sum, d) => sum + d.rowCount, 0));
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStats(); }, []);

  const cards = [
    { name: 'Total Datasets', value: datasetCount, icon: Database, color: 'text-blue-500' },
    { name: 'Active Pipelines', value: pipelineCount, icon: GitBranch, color: 'text-green-500' },
    { name: 'Total Rows', value: totalRows.toLocaleString(), icon: Activity, color: 'text-purple-500' },
    { name: 'Storage', value: 'Browser', icon: FileText, color: 'text-orange-500' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <button onClick={fetchStats} className="p-2 text-gray-400 hover:text-white rounded hover:bg-gray-700" title="Refresh">
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div key={card.name} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">{card.name}</p>
                <p className="text-3xl font-bold text-white mt-2">{card.value}</p>
              </div>
              <card.icon className={`w-12 h-12 ${card.color}`} />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold text-white mb-4">About</h2>
        <p className="text-gray-400">
          This application runs entirely in your browser. Data is stored locally using IndexedDB.
          No server required - deploy anywhere as a static site.
        </p>
      </div>
    </div>
  );
}
