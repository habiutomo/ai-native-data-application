import Papa from 'papaparse';
import * as XLSX from 'xlsx';
import { db, type Dataset } from './db';

export function parseCSV(file: File): Promise<{ data: Record<string, unknown>[]; columns: string[] }> {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const data = results.data as Record<string, unknown>[];
        const columns = results.meta.fields || [];
        resolve({ data, columns });
      },
      error: (err) => reject(err),
    });
  });
}

export function parseExcel(file: File): Promise<{ data: Record<string, unknown>[]; columns: string[] }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const workbook = XLSX.read(e.target?.result, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet);
        const columns = jsonData.length > 0 ? Object.keys(jsonData[0]) : [];
        resolve({ data: jsonData, columns });
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsArrayBuffer(file);
  });
}

export function parseJSON(file: File): Promise<{ data: Record<string, unknown>[]; columns: string[] }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        let jsonData = JSON.parse(e.target?.result as string);
        if (!Array.isArray(jsonData)) {
          jsonData = [jsonData];
        }
        const columns = jsonData.length > 0 ? Object.keys(jsonData[0]) : [];
        resolve({ data: jsonData, columns });
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

export async function uploadDataset(file: File): Promise<Dataset> {
  const ext = file.name.split('.').pop()?.toLowerCase();
  let parsed: { data: Record<string, unknown>[]; columns: string[] };

  if (ext === 'csv') {
    parsed = await parseCSV(file);
  } else if (ext === 'xlsx' || ext === 'xls') {
    parsed = await parseExcel(file);
  } else if (ext === 'json') {
    parsed = await parseJSON(file);
  } else {
    throw new Error('Unsupported file type');
  }

  const dataset: Omit<Dataset, 'id'> = {
    name: file.name.replace(/\.[^/.]+$/, ''),
    filename: file.name,
    data: parsed.data,
    columns: parsed.columns,
    rowCount: parsed.data.length,
    columnCount: parsed.columns.length,
    createdAt: new Date().toISOString(),
  };

  const id = await db.datasets.add(dataset as Dataset);
  return { ...dataset, id } as Dataset;
}

export async function getDatasetPreview(id: number, rows: number = 20): Promise<{ columns: string[]; data: Record<string, unknown>[]; shape: [number, number] }> {
  const dataset = await db.datasets.get(id);
  if (!dataset) throw new Error('Dataset not found');
  return {
    columns: dataset.columns,
    data: dataset.data.slice(0, rows),
    shape: [dataset.rowCount, dataset.columnCount],
  };
}

export async function runPipeline(pipelineId: number): Promise<{ success: boolean; message: string; rowsProcessed: number }> {
  const pipeline = await db.pipelines.get(pipelineId);
  if (!pipeline) throw new Error('Pipeline not found');

  const dataset = pipeline.datasetId ? await db.datasets.get(pipeline.datasetId) : null;

  await db.pipelines.update(pipelineId, { status: 'running' });

  try {
    let rowsProcessed = 0;

    if (dataset) {
      const config = pipeline.config as { transformations?: Array<{ type: string; column?: string; value?: unknown }> };
      let data = [...dataset.data];

      for (const transform of config.transformations || []) {
        switch (transform.type) {
          case 'filter':
            if (transform.column) {
              data = data.filter((row) => row[transform.column!] !== null && row[transform.column!] !== undefined);
            }
            break;
          case 'drop':
            if (transform.column) {
              data = data.map((row) => {
                const newRow = { ...row };
                delete newRow[transform.column!];
                return newRow;
              });
            }
            break;
          case 'rename':
            if (transform.column && transform.value) {
              data = data.map((row) => {
                const newRow = { ...row };
                const val = newRow[transform.column!];
                delete newRow[transform.column!];
                newRow[transform.value as string] = val;
                return newRow;
              });
            }
            break;
          case 'sort':
            if (transform.column) {
              data.sort((a, b) => {
                const aVal = a[transform.column!];
                const bVal = b[transform.column!];
                if (typeof aVal === 'number' && typeof bVal === 'number') return aVal - bVal;
                return String(aVal).localeCompare(String(bVal));
              });
            }
            break;
        }
      }
      rowsProcessed = data.length;
    }

    await db.pipelines.update(pipelineId, {
      status: 'completed',
      lastRun: new Date().toISOString(),
    });

    return { success: true, message: 'Pipeline completed', rowsProcessed };
  } catch (err) {
    await db.pipelines.update(pipelineId, { status: 'failed' });
    throw err;
  }
}
