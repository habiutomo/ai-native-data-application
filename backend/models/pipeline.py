from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.core.database import Base

class Pipeline(Base):
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    status = Column(String(50), default="idle")
    last_run = Column(DateTime, nullable=True)
    last_result = Column(JSON, nullable=True)
    schedule = Column(String(50), nullable=True)
    enabled = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="pipelines")
    dataset = relationship("Dataset")
    runs = relationship("PipelineRun", back_populates="pipeline")

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"))
    status = Column(String(50), default="running")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    
    pipeline = relationship("Pipeline", back_populates="runs")

class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    schedule: Optional[str] = None
    enabled: Optional[bool] = True
    dataset_id: Optional[int] = None

class PipelineResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    status: str
    last_run: Optional[datetime]
    last_result: Optional[Dict[str, Any]]
    schedule: Optional[str]
    enabled: bool
    owner_id: int
    dataset_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
