import { useEffect, useState } from 'react';
import { Database, GitBranch, BarChart3, Activity, RefreshCw } from 'lucide-react';

interface DbStats {
  total_tables: number;
  tables: Record<string, { columns: number; rows: number; has_indexes: boolean }>;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DbStats | null>(null);
  const [datasetCount, setDatasetCount] = useState(0);
  const [pipelineCount, setPipelineCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [dbRes, dsRes, plRes] = await Promise.all([
        fetch('/api/v1/database/stats'),
        fetch('/api/v1/datasets?limit=1000'),
        fetch('/api/v1/pipelines?limit=1000'),
      ]);
      if (dbRes.ok) setStats(await dbRes.json());
      if (dsRes.ok) setDatasetCount((await dsRes.json()).length);
      if (plRes.ok) setPipelineCount((await plRes.json()).length);
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
    { name: 'DB Tables', value: stats?.total_tables ?? 0, icon: BarChart3, color: 'text-purple-500' },
    {
      name: 'Total Rows',
      value: stats ? Object.values(stats.tables).reduce((s, t) => s + t.rows, 0).toLocaleString() : '0',
      icon: Activity,
      color: 'text-orange-500',
    },
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

      {stats && Object.keys(stats.tables).length > 0 && (
        <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-4">Database Tables</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 px-4 text-gray-400 font-medium">Table</th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">Columns</th>
                  <th className="text-right py-2 px-4 text-gray-400 font-medium">Rows</th>
                  <th className="text-center py-2 px-4 text-gray-400 font-medium">Indexes</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.tables).map(([name, info]) => (
                  <tr key={name} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-2 px-4 text-white font-mono">{name}</td>
                    <td className="py-2 px-4 text-gray-300 text-right">{info.columns}</td>
                    <td className="py-2 px-4 text-gray-300 text-right">{info.rows.toLocaleString()}</td>
                    <td className="py-2 px-4 text-center">
                      {info.has_indexes
                        ? <span className="text-green-400">&#10003;</span>
                        : <span className="text-gray-500">&#10007;</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
