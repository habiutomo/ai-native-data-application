# AI-Native Data Application

A comprehensive data application that runs entirely in your browser. No server required - deploy anywhere as a static site.

## Features

- **Data Analytics** - Statistical analysis, anomaly detection, correlation analysis
- **Data Pipelines** - Create and run ETL pipelines with transformations
- **ML Predictions** - RandomForest classification and regression models
- **Time Series Forecasting** - Predict future values from historical data
- **File Upload** - Support for CSV, Excel, and JSON files
- **Client-Side Storage** - Data persists in your browser using IndexedDB

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Data Processing**: PapaParse (CSV), SheetJS (Excel), danfo.js
- **ML/AI**: ml-random-forest (client-side RandomForest)
- **Storage**: IndexedDB via Dexie.js
- **Charts**: Recharts

## Project Structure

```
ai-native-data-application/
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── db.ts           # IndexedDB wrapper
│   │   │   ├── dataService.ts  # File parsing & data operations
│   │   │   ├── analytics.ts    # Statistics & analysis
│   │   │   └── ml.ts           # ML models (RandomForest)
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Datasets.tsx
│   │   │   ├── Pipelines.tsx
│   │   │   └── Analytics.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── .github/workflows/
    └── deploy.yml             # GitHub Actions auto-deploy
```

## Quick Start

1. Clone the repository
2. Install dependencies: `cd frontend && npm install`
3. Run development server: `npm run dev`
4. Open http://localhost:3000

## Deploy to GitHub Pages

1. Push to GitHub
2. Enable GitHub Pages in repository settings (Source: GitHub Actions)
3. Every push to `main` will auto-deploy

Or deploy manually:
```bash
cd frontend
npm run build
# Upload dist/ folder to any static hosting
```

## How It Works

- All data processing happens in your browser
- Files are parsed client-side (no server upload)
- Data stored in IndexedDB (persists across sessions)
- ML models run using JavaScript (no Python required)
- No backend server needed

## License

MIT
