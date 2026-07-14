import { useState, useEffect } from 'react';
import { Brain, TrendingUp, Target, Sparkles, Database } from 'lucide-react';
import { apiFetch } from '../lib/api';

interface Dataset {
  id: number;
  name: string;
  filename: string;
}

interface AnalysisResult {
  summary: string;
  insights: string[];
  statistics: Record<string, unknown>;
  visualizations: Record<string, unknown>;
  anomalies: Record<string, unknown>;
}

export default function Analytics() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null);
  const [analysisType, setAnalysisType] = useState<string>('analyze');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // extra params
  const [targetColumn, setTargetColumn] = useState('');
  const [dateColumn, setDateColumn] = useState('');
  const [valueColumn, setValueColumn] = useState('');
  const [periods, setPeriods] = useState(30);
  const [context, setContext] = useState('');

  useEffect(() => {
    apiFetch('/api/v1/datasets?limit=1000')
      .then((r) => r.json())
      .then(setDatasets)
      .catch(() => {});
  }, []);

  const analysisTypes = [
    { id: 'analyze', name: 'AI Analysis', icon: Brain, description: 'Get AI-powered insights' },
    { id: 'predict', name: 'Prediction', icon: TrendingUp, description: 'Build predictive models' },
    { id: 'forecast', name: 'Forecasting', icon: Target, description: 'Time series forecasting' },
    { id: 'enrich', name: 'Data Enrichment', icon: Sparkles, description: 'Enhance your data' },
  ];

  const handleRun = async () => {
    if (!selectedDataset) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let res: Response;
      switch (analysisType) {
        case 'analyze':
          res = await apiFetch(`/api/v1/analytics/analyze/${selectedDataset}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ context: context || null }),
          });
          break;
        case 'predict':
          if (!targetColumn) { setError('Target column is required'); setLoading(false); return; }
          res = await apiFetch(`/api/v1/analytics/predict/${selectedDataset}?target_column=${encodeURIComponent(targetColumn)}&task_type=auto`, { method: 'POST' });
          break;
        case 'forecast':
          if (!dateColumn || !valueColumn) { setError('Date and value columns are required'); setLoading(false); return; }
          res = await apiFetch(`/api/v1/analytics/forecast/${selectedDataset}?date_column=${encodeURIComponent(dateColumn)}&value_column=${encodeURIComponent(valueColumn)}&periods=${periods}`, { method: 'POST' });
          break;
        case 'enrich':
          res = await apiFetch(`/api/v1/analytics/enrich/${selectedDataset}`, { method: 'POST' });
          break;
        default:
          setLoading(false);
          return;
      }
      if (res.ok) {
        setResult(await res.json());
      } else {
        const err = await res.json();
        setError(err.detail || 'Analysis failed');
      }
    } catch {
      setError('Network error');
    }
    setLoading(false);
  };

  const renderResult = (data: Record<string, unknown>) => {
    if (data.summary) {
      const a = data as unknown as AnalysisResult;
      return (
        <>
          <div className="mb-6">
            <h3 className="text-gray-400 text-sm mb-2">Summary</h3>
            <p className="text-white">{a.summary}</p>
          </div>
          {a.insights && a.insights.length > 0 && (
            <div className="mb-6">
              <h3 className="text-gray-400 text-sm mb-2">Key Insights</h3>
              <ul className="space-y-2">
                {a.insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start text-white">
                    <span className="text-blue-500 mr-2">&#8226;</span> {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {a.statistics && (
            <div>
              <h3 className="text-gray-400 text-sm mb-2">Statistics</h3>
              <pre className="bg-gray-900 rounded p-4 text-gray-300 text-sm overflow-auto">{JSON.stringify(a.statistics, null, 2)}</pre>
            </div>
          )}
        </>
      );
    }
    return (
      <pre className="bg-gray-900 rounded p-4 text-gray-300 text-sm overflow-auto whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">AI Analytics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          {/* Dataset selector */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
              <Database className="w-5 h-5 mr-2" /> Dataset
            </h2>
            <select
              value={selectedDataset ?? ''}
              onChange={(e) => setSelectedDataset(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">Select a dataset...</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.filename})</option>
              ))}
            </select>
          </div>

          {/* Analysis type */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Analysis Type</h2>
            <div className="space-y-3">
              {analysisTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => { setAnalysisType(type.id); setResult(null); setError(null); }}
                  className={`w-full flex items-center p-4 rounded-lg border ${
                    analysisType === type.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <type.icon className={`w-6 h-6 mr-3 ${analysisType === type.id ? 'text-blue-500' : 'text-gray-400'}`} />
                  <div className="text-left">
                    <p className="text-white font-medium">{type.name}</p>
                    <p className="text-gray-400 text-sm">{type.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Extra params */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-lg font-semibold text-white mb-4">Parameters</h2>
            {analysisType === 'analyze' && (
              <div>
                <label className="block text-gray-400 text-sm mb-1">Context (optional)</label>
                <textarea value={context} onChange={(e) => setContext(e.target.value)} rows={2}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="Additional context for the AI..." />
              </div>
            )}
            {analysisType === 'predict' && (
              <div>
                <label className="block text-gray-400 text-sm mb-1">Target Column *</label>
                <input value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                  placeholder="e.g. price" />
              </div>
            )}
            {analysisType === 'forecast' && (
              <div className="space-y-3">
                <div>
                  <label className="block text-gray-400 text-sm mb-1">Date Column *</label>
                  <input value={dateColumn} onChange={(e) => setDateColumn(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                    placeholder="e.g. date" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-1">Value Column *</label>
                  <input value={valueColumn} onChange={(e) => setValueColumn(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                    placeholder="e.g. sales" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-1">Periods</label>
                  <input type="number" value={periods} onChange={(e) => setPeriods(Number(e.target.value))} min={1} max={365}
                    className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
              </div>
            )}
            {analysisType === 'enrich' && (
              <p className="text-gray-500 text-sm">Will automatically enrich the dataset using AI.</p>
            )}
          </div>

          <button
            onClick={handleRun}
            disabled={!selectedDataset || loading}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        {/* Results */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 min-h-[500px]">
            {result ? (
              <>
                <h2 className="text-lg font-semibold text-white mb-4">Results</h2>
                {renderResult(result)}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-400 min-h-[400px]">
                <Brain className="w-16 h-16 mb-4" />
                <p>Select a dataset and analysis type to get started</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
