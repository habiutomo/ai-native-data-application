from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd

from backend.core.database import get_db
from backend.models.dataset import Dataset
from backend.ai.analyzer import DataAnalyzer
from backend.ai.predictor import DataPredictor
from backend.ai.enricher import DataEnricher

router = APIRouter()
analyzer = DataAnalyzer()
predictor = DataPredictor()
enricher = DataEnricher()

@router.post("/analyze/{dataset_id}")
async def analyze_dataset(
    dataset_id: int,
    context: Optional[str] = None,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    result = await analyzer.analyze(df, context)
    
    return {
        "summary": result.summary,
        "insights": result.insights,
        "statistics": result.statistics,
        "visualizations": result.visualizations,
        "anomalies": result.anomalies
    }

@router.post("/predict/{dataset_id}")
async def predict(
    dataset_id: int,
    target_column: str,
    task_type: str = "auto",
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    
    if target_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{target_column}' not found")
    
    result = await predictor.predict(df, target_column, task_type)
    
    return result

@router.post("/forecast/{dataset_id}")
async def forecast(
    dataset_id: int,
    date_column: str,
    value_column: str,
    periods: int = 30,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    
    if date_column not in df.columns or value_column not in df.columns:
        raise HTTPException(status_code=400, detail="Invalid column names")
    
    result = await predictor.forecast(df, date_column, value_column, periods)
    
    return result

@router.post("/enrich/{dataset_id}")
async def enrich_dataset(
    dataset_id: int,
    rules: Optional[List[Dict[str, Any]]] = None,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    enriched_df = await enricher.enrich(df, rules)
    
    enriched_path = dataset.file_path.replace('.csv', '_enriched.csv')
    enriched_df.to_csv(enriched_path, index=False)
    
    return {
        "original_shape": df.shape,
        "enriched_shape": enriched_df.shape,
        "new_columns": list(set(enriched_df.columns) - set(df.columns)),
        "file_path": enriched_path
    }

@router.get("/visualizations/{dataset_id}")
async def get_visualizations(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    result = await analyzer.analyze(df)
    
    return {
        "visualizations": result.visualizations,
        "statistics": result.statistics
    }

@router.post("/correlation/{dataset_id}")
async def correlation_analysis(
    dataset_id: int,
    columns: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    
    if columns:
        numeric_df = df[columns].select_dtypes(include=['number'])
    else:
        numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty:
        raise HTTPException(status_code=400, detail="No numeric columns found")
    
    correlation_matrix = numeric_df.corr().to_dict()
    
    strong_correlations = []
    for i, col1 in enumerate(correlation_matrix.keys()):
        for j, col2 in enumerate(correlation_matrix.keys()):
            if i < j:
                corr_value = correlation_matrix[col1][col2]
                if abs(corr_value) > 0.7:
                    strong_correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": corr_value
                    })
    
    return {
        "correlation_matrix": correlation_matrix,
        "strong_correlations": strong_correlations,
        "columns_analyzed": list(correlation_matrix.keys())
    }
