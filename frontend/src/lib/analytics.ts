import { db } from './db';

interface ColumnStats {
  type: 'numeric' | 'categorical' | 'datetime';
  count: number;
  missing: number;
  unique: number;
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
  median?: number;
  percentiles?: { p25: number; p75: number };
  topValues?: Record<string, number>;
}

export interface AnalysisResult {
  summary: string;
  insights: string[];
  statistics: Record<string, ColumnStats>;
  anomalies: { column: string; indices: number[]; values: unknown[] }[];
  visualizations: { type: string; columns: string[]; description: string }[];
}

function isNumeric(value: unknown): boolean {
  return typeof value === 'number' || (typeof value === 'string' && value !== '' && !isNaN(Number(value)));
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number') return value;
  if (typeof value === 'string' && value !== '') {
    const n = Number(value);
    return isNaN(n) ? null : n;
  }
  return null;
}

function calculateStats(values: unknown[]): ColumnStats {
  const numericValues = values.map(toNumber).filter((v): v is number => v !== null);
  const nonNullValues = values.filter((v) => v !== null && v !== undefined && v !== '');
  const uniqueValues = new Set(values.map(String));

  const isNum = numericValues.length > nonNullValues.length * 0.5;

  if (isNum && numericValues.length > 0) {
    const sorted = [...numericValues].sort((a, b) => a - b);
    const n = sorted.length;
    const mean = sorted.reduce((s, v) => s + v, 0) / n;
    const std = Math.sqrt(sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / n);
    const median = n % 2 === 0 ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2 : sorted[Math.floor(n / 2)];

    return {
      type: 'numeric',
      count: values.length,
      missing: values.length - numericValues.length,
      unique: uniqueValues.size,
      mean,
      std,
      min: sorted[0],
      max: sorted[n - 1],
      median,
      percentiles: {
        p25: sorted[Math.floor(n * 0.25)],
        p75: sorted[Math.floor(n * 0.75)],
      },
    };
  }

  const topValues: Record<string, number> = {};
  nonNullValues.forEach((v) => {
    const key = String(v);
    topValues[key] = (topValues[key] || 0) + 1;
  });

  return {
    type: 'categorical',
    count: values.length,
    missing: values.length - nonNullValues.length,
    unique: uniqueValues.size,
    topValues,
  };
}

function detectAnomalies(stats: Record<string, ColumnStats>, data: Record<string, unknown>[]): { column: string; indices: number[]; values: unknown[] }[] {
  const anomalies: { column: string; indices: number[]; values: unknown[] }[] = [];

  for (const [col, stat] of Object.entries(stats)) {
    if (stat.type !== 'numeric' || stat.mean === undefined || stat.std === undefined || stat.std === 0) continue;

    const zScores = data.map((row) => {
      const val = toNumber(row[col]);
      if (val === null) return null;
      return Math.abs((val - stat.mean!) / stat.std!);
    });

    const outlierIndices: number[] = [];
    const outlierValues: unknown[] = [];
    zScores.forEach((z, i) => {
      if (z !== null && z > 3) {
        outlierIndices.push(i);
        outlierValues.push(data[i][col]);
      }
    });

    if (outlierIndices.length > 0) {
      anomalies.push({ column: col, indices: outlierIndices, values: outlierValues });
    }
  }

  return anomalies;
}

function calculateCorrelation(data: Record<string, unknown>[], columns: string[]): { col1: string; col2: string; correlation: number }[] {
  const numericCols = columns.filter((col) => {
    const values = data.map((row) => row[col]).filter(isNumeric);
    return values.length > data.length * 0.5;
  });

  const correlations: { col1: string; col2: string; correlation: number }[] = [];

  for (let i = 0; i < numericCols.length; i++) {
    for (let j = i + 1; j < numericCols.length; j++) {
      const x = data.map((row) => toNumber(row[numericCols[i]])!).filter((v) => !isNaN(v));
      const y = data.map((row) => toNumber(row[numericCols[j]])!).filter((v) => !isNaN(v));

      const n = Math.min(x.length, y.length);
      if (n < 2) continue;

      const xArr = x.slice(0, n);
      const yArr = y.slice(0, n);

      const xMean = xArr.reduce((s, v) => s + v, 0) / n;
      const yMean = yArr.reduce((s, v) => s + v, 0) / n;

      let num = 0, denX = 0, denY = 0;
      for (let k = 0; k < n; k++) {
        const dx = xArr[k] - xMean;
        const dy = yArr[k] - yMean;
        num += dx * dy;
        denX += dx * dx;
        denY += dy * dy;
      }

      const den = Math.sqrt(denX * denY);
      const corr = den === 0 ? 0 : num / den;
      correlations.push({ col1: numericCols[i], col2: numericCols[j], correlation: corr });
    }
  }

  return correlations.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
}

function generateInsights(stats: Record<string, ColumnStats>, anomalies: { column: string; indices: number[] }[]): string[] {
  const insights: string[] = [];
  const columns = Object.keys(stats);
  const numericCols = columns.filter((c) => stats[c].type === 'numeric');

  insights.push(`Dataset has ${stats[columns[0]]?.count || 0} rows and ${columns.length} columns.`);
  insights.push(`${numericCols.length} numeric columns, ${columns.length - numericCols.length} categorical columns.`);

  const highMissing = columns.filter((c) => stats[c].missing > 0);
  if (highMissing.length > 0) {
    insights.push(`Missing values found in ${highMissing.length} column(s): ${highMissing.join(', ')}.`);
  }

  if (anomalies.length > 0) {
    insights.push(`${anomalies.length} column(s) have potential outliers (z-score > 3).`);
  }

  if (numericCols.length >= 2) {
    const correlations = calculateCorrelation([], numericCols);
    const strong = correlations.filter((c) => Math.abs(c.correlation) > 0.7);
    if (strong.length > 0) {
      insights.push(`Strong correlation found between ${strong[0].col1} and ${strong[0].col2} (${strong[0].correlation.toFixed(2)}).`);
    }
  }

  return insights;
}

export async function analyzeDataset(datasetId: number, context?: string): Promise<AnalysisResult> {
  const dataset = await db.datasets.get(datasetId);
  if (!dataset) throw new Error('Dataset not found');

  const { data, columns } = dataset;
  const stats: Record<string, ColumnStats> = {};
  columns.forEach((col) => {
    stats[col] = calculateStats(data.map((row) => row[col]));
  });

  const anomalies = detectAnomalies(stats, data);
  const insights = generateInsights(stats, anomalies);

  if (context) {
    insights.push(`Additional context: ${context}`);
  }

  const numericCols = columns.filter((c) => stats[c].type === 'numeric');
  const visualizations: { type: string; columns: string[]; description: string }[] = [];

  if (numericCols.length > 0) {
    visualizations.push({ type: 'histogram', columns: [numericCols[0]], description: `Distribution of ${numericCols[0]}` });
  }
  if (numericCols.length >= 2) {
    visualizations.push({ type: 'scatter', columns: [numericCols[0], numericCols[1]], description: `Scatter plot: ${numericCols[0]} vs ${numericCols[1]}` });
  }

  return {
    summary: `Analysis of "${dataset.name}": ${data.length} rows, ${columns.length} columns.`,
    insights,
    statistics: stats,
    anomalies,
    visualizations,
  };
}

export async function enrichDataset(datasetId: number): Promise<{ success: boolean; message: string; enrichedRows: number }> {
  const dataset = await db.datasets.get(datasetId);
  if (!dataset) throw new Error('Dataset not found');

  const enrichedData = dataset.data.map((row) => {
    const newRow = { ...row };

    dataset.columns.forEach((col) => {
      if (newRow[col] === null || newRow[col] === undefined || newRow[col] === '') {
        const values = dataset.data
          .map((r) => r[col])
          .filter((v) => v !== null && v !== undefined && v !== '');
        if (values.length > 0) {
          const numValues = values.map(toNumber).filter((v): v is number => v !== null);
          if (numValues.length > values.length * 0.5) {
            newRow[col] = numValues.reduce((s, v) => s + v, 0) / numValues.length;
          } else {
            const freq: Record<string, number> = {};
            values.forEach((v) => { freq[String(v)] = (freq[String(v)] || 0) + 1; });
            newRow[col] = Object.entries(freq).sort((a, b) => b[1] - a[1])[0][0];
          }
        }
      }
    });

    return newRow;
  });

  await db.datasets.update(datasetId, { data: enrichedData });

  return {
    success: true,
    message: `Enriched ${dataset.name} - filled missing values`,
    enrichedRows: enrichedData.length,
  };
}
