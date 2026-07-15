import Dexie, { type Table } from 'dexie';

export interface Dataset {
  id?: number;
  name: string;
  filename: string;
  data: Record<string, unknown>[];
  columns: string[];
  rowCount: number;
  columnCount: number;
  createdAt: string;
}

export interface Pipeline {
  id?: number;
  name: string;
  description: string | null;
  status: string;
  schedule: string | null;
  lastRun: string | null;
  enabled: boolean;
  datasetId: number | null;
  config: Record<string, unknown>;
}

class AppDatabase extends Dexie {
  datasets!: Table<Dataset>;
  pipelines!: Table<Pipeline>;

  constructor() {
    super('ai-native-db');
    this.version(1).stores({
      datasets: '++id, name, filename, createdAt',
      pipelines: '++id, name, status, datasetId',
    });
  }
}

export const db = new AppDatabase();

export async function getDatasets(): Promise<Dataset[]> {
  return db.datasets.toArray();
}

export async function getDataset(id: number): Promise<Dataset | undefined> {
  return db.datasets.get(id);
}

export async function addDataset(dataset: Omit<Dataset, 'id'>): Promise<number> {
  return db.datasets.add(dataset as Dataset);
}

export async function deleteDataset(id: number): Promise<void> {
  await db.datasets.delete(id);
}

export async function getPipelines(): Promise<Pipeline[]> {
  return db.pipelines.toArray();
}

export async function getPipeline(id: number): Promise<Pipeline | undefined> {
  return db.pipelines.get(id);
}

export async function addPipeline(pipeline: Omit<Pipeline, 'id'>): Promise<number> {
  return db.pipelines.add(pipeline as Pipeline);
}

export async function updatePipeline(id: number, changes: Partial<Pipeline>): Promise<void> {
  await db.pipelines.update(id, changes);
}

export async function deletePipeline(id: number): Promise<void> {
  await db.pipelines.delete(id);
}
