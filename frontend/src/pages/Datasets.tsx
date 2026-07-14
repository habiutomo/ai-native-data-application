import { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Trash2, BarChart3, Eye, X } from 'lucide-react';

interface Dataset {
  id: number;
  name: string;
  filename: string;
  row_count: number;
  column_count: number;
  created_at: string;
}

interface PreviewData {
  columns: string[];
  data: Record<string, unknown>[];
  shape: [number, number];
}

interface AnalysisResult {
  summary: string;
  insights: string[];
  statistics: Record<string, unknown>;
  visualizations: Record<string, unknown>;
  anomalies: Record<string, unknown>;
}

export default function Datasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<{ dataset: Dataset; data: PreviewData } | null>(null);
  const [analysis, setAnalysis] = useState<{ dataset: Dataset; result: AnalysisResult } | null>(null);
  const [analyzing, setAnalyzing] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDatasets = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/datasets?limit=1000');
      if (res.ok) setDatasets(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadDatasets(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/v1/datasets/upload', { method: 'POST', body: formData });
      if (res.ok) {
        const newDataset = await res.json();
        setDatasets((prev) => [newDataset, ...prev]);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this dataset?')) return;
    const res = await fetch(`/api/v1/datasets/${id}`, { method: 'DELETE' });
    if (res.ok) setDatasets((prev) => prev.filter((d) => d.id !== id));
  };

  const handlePreview = async (dataset: Dataset) => {
    const res = await fetch(`/api/v1/datasets/${dataset.id}/preview?rows=20`);
    if (res.ok) setPreview({ dataset, data: await res.json() });
  };

  const handleAnalyze = async (dataset: Dataset) => {
    setAnalyzing(dataset.id);
    try {
      const res = await fetch(`/api/v1/datasets/${dataset.id}/analyze`, { method: 'POST' });
      if (res.ok) setAnalysis({ dataset, result: await res.json() });
    } catch { /* ignore */ }
    setAnalyzing(null);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Datasets</h1>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <Upload className="w-5 h-5 mr-2" />
          {uploading ? 'Uploading...' : 'Upload Dataset'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json"
          onChange={handleUpload}
          className="hidden"
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading datasets...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((dataset) => (
            <div key={dataset.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  <FileText className="w-10 h-10 text-blue-500 mr-3 shrink-0" />
                  <div className="min-w-0">
                    <h3 className="text-white font-medium truncate">{dataset.name}</h3>
                    <p className="text-gray-400 text-sm truncate">{dataset.filename}</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Rows</p>
                  <p className="text-white">{dataset.row_count?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400">Columns</p>
                  <p className="text-white">{dataset.column_count}</p>
                </div>
              </div>
              <p className="text-gray-500 text-xs mt-2">
                {new Date(dataset.created_at).toLocaleDateString()}
              </p>
              <div className="mt-4 flex space-x-2">
                <button
                  onClick={() => handlePreview(dataset)}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  <Eye className="w-4 h-4 mr-1" /> Preview
                </button>
                <button
                  onClick={() => handleAnalyze(dataset)}
                  disabled={analyzing === dataset.id}
                  className="flex-1 flex items-center justify-center px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                >
                  <BarChart3 className="w-4 h-4 mr-1" />
                  {analyzing === dataset.id ? '...' : 'Analyze'}
                </button>
                <button
                  onClick={() => handleDelete(dataset.id)}
                  className="px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {datasets.length === 0 && (
            <div className="col-span-full text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
              <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No datasets uploaded yet</p>
              <p className="text-gray-500 text-sm mt-2">Upload a CSV, Excel, or JSON file to get started</p>
            </div>
          )}
        </div>
      )}

      {/* Preview Modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setPreview(null)}>
          <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-5xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-white font-semibold">Preview: {preview.dataset.name} ({preview.data.shape[0]} rows)</h2>
              <button onClick={() => setPreview(null)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="overflow-auto p-4">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-700">
                    {preview.data.columns.map((col) => (
                      <th key={col} className="py-2 px-3 text-gray-400 font-medium whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.data.data.map((row, i) => (
                    <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                      {preview.data.columns.map((col) => (
                        <td key={col} className="py-2 px-3 text-gray-300 whitespace-nowrap">{String(row[col] ?? '')}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Modal */}
      {analysis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => setAnalysis(null)}>
          <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-3xl max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h2 className="text-white font-semibold">Analysis: {analysis.dataset.name}</h2>
              <button onClick={() => setAnalysis(null)} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="overflow-auto p-6 space-y-6">
              <div>
                <h3 className="text-gray-400 text-sm mb-2">Summary</h3>
                <p className="text-white">{analysis.result.summary}</p>
              </div>
              {analysis.result.insights && analysis.result.insights.length > 0 && (
                <div>
                  <h3 className="text-gray-400 text-sm mb-2">Key Insights</h3>
                  <ul className="space-y-2">
                    {analysis.result.insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start text-white">
                        <span className="text-blue-500 mr-2">&#8226;</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {analysis.result.statistics && (
                <div>
                  <h3 className="text-gray-400 text-sm mb-2">Statistics</h3>
                  <pre className="bg-gray-900 rounded p-4 text-gray-300 text-sm overflow-auto">
                    {JSON.stringify(analysis.result.statistics, null, 2)}
                  </pre>
                </div>
              )}
              {analysis.result.anomalies && (
                <div>
                  <h3 className="text-gray-400 text-sm mb-2">Anomalies</h3>
                  <pre className="bg-gray-900 rounded p-4 text-gray-300 text-sm overflow-auto">
                    {JSON.stringify(analysis.result.anomalies, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
