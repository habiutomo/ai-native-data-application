from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import os
import json

from backend.core.database import get_db
from backend.core.security import decode_token
from backend.models.dataset import Dataset, DatasetCreate, DatasetResponse
from backend.ai.analyzer import DataAnalyzer

router = APIRouter()
analyzer = DataAnalyzer()

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file.filename.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        dataset = Dataset(
            name=name or file.filename,
            description=description,
            filename=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            row_count=len(df),
            column_count=len(df.columns),
            schema_info=df.dtypes.to_dict(),
            extra_metadata={
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict()
            },
            owner_id=1
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return dataset
        
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    datasets = db.query(Dataset).offset(skip).limit(limit).all()
    return datasets

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/{dataset_id}/preview")
async def preview_dataset(dataset_id: int, rows: int = 10, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    return {
        "columns": df.columns.tolist(),
        "data": df.head(rows).to_dict('records'),
        "shape": df.shape
    }

@router.post("/{dataset_id}/analyze")
async def analyze_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = pd.read_csv(dataset.file_path)
    result = await analyzer.analyze(df)
    
    return {
        "summary": result.summary,
        "insights": result.insights,
        "statistics": result.statistics,
        "visualizations": result.visualizations,
        "anomalies": result.anomalies
    }

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}
