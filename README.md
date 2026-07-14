# AI-Native Data Application

A comprehensive data application powered by AI capabilities, featuring analytics dashboards, database management, data pipelines, and intelligent data processing.

## Features

- **AI Analytics Dashboard** - Real-time data visualization with AI-generated insights
- **Smart Database Manager** - AI-optimized queries and schema management
- **Intelligent Data Pipeline** - Automated ETL with AI transformation
- **AI Data Processing** - Smart data cleaning, enrichment, and analysis

## Tech Stack

- **Backend**: Python, FastAPI
- **AI/ML**: Ollama (local LLM), scikit-learn, pandas
- **Database**: PostgreSQL (configurable)
- **Frontend**: React, TailwindCSS, Recharts
- **Task Queue**: Celery, Redis

## Project Structure

```
ai-native-data-app/
├── backend/
│   ├── api/              # FastAPI routes
│   ├── core/             # Configuration and utilities
│   ├── ai/               # AI/ML modules
│   ├── pipeline/         # Data pipeline
│   ├── database/         # Database management
│   └── models/           # Data models
├── frontend/             # React application
├── docker/               # Docker configurations
└── docs/                 # Documentation
```

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run the application: `uvicorn backend.main:app --reload`

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key
```

## License

MIT
