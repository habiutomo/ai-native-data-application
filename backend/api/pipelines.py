from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd

from backend.core.database import get_db
from backend.models.pipeline import Pipeline, PipelineCreate, PipelineResponse
from backend.models.dataset import Dataset
from backend.pipeline.etl import ETLPipeline
from backend.pipeline.transformer import DataTransformer
from backend.pipeline.scheduler import PipelineScheduler, ScheduleFrequency

router = APIRouter()
scheduler = PipelineScheduler()

@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    db: Session = Depends(get_db)
):
    pipeline = Pipeline(
        name=pipeline_data.name,
        description=pipeline_data.description,
        config=pipeline_data.config,
        schedule=pipeline_data.schedule,
        enabled=pipeline_data.enabled,
        dataset_id=pipeline_data.dataset_id,
        owner_id=1
    )
    
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    
    return pipeline

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    pipelines = db.query(Pipeline).offset(skip).limit(limit).all()
    return pipelines

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline

@router.post("/{pipeline_id}/run")
async def run_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if pipeline.dataset_id:
        dataset = db.query(Dataset).filter(Dataset.id == pipeline.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_csv(dataset.file_path)
    else:
        raise HTTPException(status_code=400, detail="No dataset associated with pipeline")
    
    etl = ETLPipeline()
    
    config = pipeline.config
    transformations = config.get('transformations', [])
    
    for transform in transformations:
        etl.add_step(
            name=transform.get('name', 'unnamed'),
            function=lambda data, **params: DataTransformer().transform(data, [params]),
            params=transform
        )
    
    result = await etl.execute(df)
    
    pipeline.status = "completed" if result.success else "failed"
    pipeline.last_result = {
        "success": result.success,
        "metadata": result.metadata,
        "execution_time": result.execution_time
    }
    db.commit()
    
    return {
        "pipeline_id": pipeline_id,
        "success": result.success,
        "execution_time": result.execution_time,
        "metadata": result.metadata,
        "errors": result.errors
    }

@router.post("/{pipeline_id}/schedule")
async def schedule_pipeline(
    pipeline_id: int,
    frequency: str = "daily",
    db: Session = Depends(get_db)
):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    freq_map = {
        "hourly": ScheduleFrequency.HOURLY,
        "daily": ScheduleFrequency.DAILY,
        "weekly": ScheduleFrequency.WEEKLY,
        "monthly": ScheduleFrequency.MONTHLY
    }
    
    schedule_freq = freq_map.get(frequency, ScheduleFrequency.DAILY)
    
    scheduler.schedule(
        task_id=f"pipeline_{pipeline_id}",
        name=pipeline.name,
        function=lambda: run_pipeline(pipeline_id),
        frequency=schedule_freq
    )
    
    pipeline.schedule = frequency
    db.commit()
    
    return {"message": f"Pipeline scheduled to run {frequency}"}

@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: int, db: Session = Depends(get_db)):
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    scheduler.unschedule(f"pipeline_{pipeline_id}")
    
    db.delete(pipeline)
    db.commit()
    
    return {"message": "Pipeline deleted successfully"}
