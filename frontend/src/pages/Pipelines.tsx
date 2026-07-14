import { useState, useEffect } from 'react';
import { Plus, Play, Trash2, Settings, X, Clock } from 'lucide-react';

interface Pipeline {
  id: number;
  name: string;
  description: string | null;
  status: string;
  schedule: string | null;
  last_run: string | null;
  enabled: boolean;
  dataset_id: number | null;
  config: Record<string, unknown>;
}

interface Dataset {
  id: number;
  name: string;
}

export default function Pipelines() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [running, setRunning] = useState<number | null>(null);
  const [runResult, setRunResult] = useState<{ pipelineId: number; result: Record<string, unknown> } | null>(null);

  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newDatasetId, setNewDatasetId] = useState<number | ''>('');
  const [newSchedule, setNewSchedule] = useState('');
  const [newConfig, setNewConfig] = useState('{\n  "transformations": []\n}');

  const statusColors: Record<string, string> = {
    idle: 'bg-gray-500',
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500',
  };

  const load = async () => {
    setLoading(true);
    try {
      const [pRes, dRes] = await Promise.all([
        fetch('/api/v1/pipelines?limit=1000'),
        fetch('/api/v1/datasets?limit=1000'),
      ]);
      if (pRes.ok) setPipelines(await pRes.json());
      if (dRes.ok) setDatasets(await dRes.json());
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    let config: Record<string, unknown>;
    try {
      config = JSON.parse(newConfig);
    } catch {
      alert('Invalid JSON config');
      return;
    }
    const body = {
      name: newName,
      description: newDesc || null,
      config,
      schedule: newSchedule || null,
      dataset_id: newDatasetId || null,
    };
    const res = await fetch('/api/v1/pipelines/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      const created = await res.json();
      setPipelines((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setNewName(''); setNewDesc(''); setNewDatasetId(''); setNewSchedule('');
      setNewConfig('{\n  "transformations": []\n}');
    }
  };

  const handleRun = async (id: number) => {
    setRunning(id);
    try {
      const res = await fetch(`/api/v1/pipelines/${id}/run`, { method: 'POST' });
      if (res.ok) {
        const result = await res.json();
        setRunResult({ pipelineId: id, result });
        setPipelines((prev) =>
          prev.map((p) =>
            p.id === id ? { ...p, status: result.success ? 'completed' : 'failed', last_run: new Date().toISOString() } : p
          )
        );
      }
    } catch { /* ignore */ }
    setRunning(null);
  };

  const handleSchedule = async (id: number, freq: string) => {
    await fetch(`/api/v1/pipelines/${id}/schedule?frequency=${freq}`, { method: 'POST' });
    setPipelines((prev) => prev.map((p) => (p.id === id ? { ...p, schedule: freq } : p)));
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this pipeline?')) return;
    await fetch(`/api/v1/pipelines/${id}`, { method: 'DELETE' });
    setPipelines((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Data Pipelines</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5 mr-2" />
          Create Pipeline
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading pipelines...</div>
      ) : (
        <div className="space-y-4">
          {pipelines.map((pipeline) => (
            <div key={pipeline.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full ${statusColors[pipeline.status] || 'bg-gray-500'} mr-3`} />
                  <div>
                    <h3 className="text-white font-medium">{pipeline.name}</h3>
                    <p className="text-gray-400 text-sm">
                      Status: <span className="capitalize">{pipeline.status}</span>
                      {pipeline.schedule && <> &middot; <Clock className="w-3 h-3 inline" /> {pipeline.schedule}</>}
                    </p>
                    {pipeline.description && <p className="text-gray-500 text-sm mt-1">{pipeline.description}</p>}
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => handleRun(pipeline.id)}
                    disabled={running === pipeline.id}
                    className="p-2 text-gray-400 hover:text-green-500 disabled:opacity-50"
                    title="Run"
                  >
                    <Play className="w-5 h-5" />
                  </button>
                  <div className="relative group">
                    <button className="p-2 text-gray-400 hover:text-blue-500" title="Schedule">
                      <Settings className="w-5 h-5" />
                    </button>
                    <div className="absolute right-0 top-full mt-1 bg-gray-700 rounded-lg border border-gray-600 py-1 hidden group-hover:block z-10 whitespace-nowrap">
                      {['hourly', 'daily', 'weekly', 'monthly'].map((f) => (
                        <button key={f} onClick={() => handleSchedule(pipeline.id, f)}
                          className="block w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-600 capitalize">
                          {f}
                        </button>
                      ))}
                      {pipeline.schedule && (
                        <button onClick={() => handleSchedule(pipeline.id, '')}
                          className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-600">
                          Remove schedule
                        </button>
                      )}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(pipeline.id)} className="p-2 text-gray-400 hover:text-red-500" title="Delete">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
              {pipeline.last_run && (
                <p className="text-gray-500 text-sm mt-3">Last run: {new Date(pipeline.last_run).toLocaleString()}</p>
              )}
            </div>
          ))}
          {pipelines.length === 0 && (
            <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
              <Settings className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No pipelines configured</p>
              <p className="text-gray-500 text-sm mt-2">Create a pipeline to automate your data workflows</p>
            </div>
          )}
        </div>
      )}

      {/* Run Result Modal */}
      {runResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setRunResult(null)}>
          <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-2xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-white font-semibold">Run Result</h2>
              <button onClick={() => setRunResult(null)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="overflow-auto p-6">
              <pre className="bg-gray-900 rounded p-4 text-gray-300 text-sm overflow-auto">
                {JSON.stringify(runResult.result, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-white font-semibold">Create Pipeline</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Name *</label>
                <input value={newName} onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  placeholder="My Pipeline" />
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">Description</label>
                <input value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Optional description" />
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">Dataset</label>
                <select value={newDatasetId} onChange={(e) => setNewDatasetId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500">
                  <option value="">None</option>
                  {datasets.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">Schedule</label>
                <select value={newSchedule} onChange={(e) => setNewSchedule(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500">
                  <option value="">Manual</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-1">Config (JSON)</label>
                <textarea value={newConfig} onChange={(e) => setNewConfig(e.target.value)} rows={4}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <button onClick={handleCreate} disabled={!newName}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
