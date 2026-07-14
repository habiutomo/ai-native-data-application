from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    schema_info = Column(JSON, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="datasets")

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    filename: str
    file_path: str
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    schema_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    filename: str
    file_size: Optional[int]
    row_count: Optional[int]
    column_count: Optional[int]
    schema_info: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
