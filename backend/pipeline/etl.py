import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import asyncio

from backend.pipeline.transformer import DataTransformer
from backend.ai.analyzer import DataAnalyzer
from backend.ai.enricher import DataEnricher

@dataclass
class PipelineStep:
    name: str
    function: Callable
    params: Dict[str, Any] = None
    enabled: bool = True

@dataclass
class PipelineResult:
    success: bool
    data: Optional[pd.DataFrame]
    errors: List[str]
    metadata: Dict[str, Any]
    execution_time: float

class ETLPipeline:
    def __init__(self):
        self.steps: List[PipelineStep] = []
        self.transformer = DataTransformer()
        self.analyzer = DataAnalyzer()
        self.enricher = DataEnricher()
        self.history: List[PipelineResult] = []
    
    def add_step(self, name: str, function: Callable, params: Dict[str, Any] = None) -> 'ETLPipeline':
        self.steps.append(PipelineStep(name=name, function=function, params=params or {}))
        return self
    
    async def execute(self, data: pd.DataFrame) -> PipelineResult:
        start_time = datetime.now()
        errors = []
        current_data = data.copy()
        
        logger.info(f"Starting pipeline with {len(self.steps)} steps")
        
        for step in self.steps:
            if not step.enabled:
                logger.info(f"Skipping disabled step: {step.name}")
                continue
            
            try:
                logger.info(f"Executing step: {step.name}")
                
                if asyncio.iscoroutinefunction(step.function):
                    current_data = await step.function(current_data, **step.params)
                else:
                    current_data = step.function(current_data, **step.params)
                
                logger.info(f"Step {step.name} completed. Shape: {current_data.shape}")
                
            except Exception as e:
                error_msg = f"Error in step {step.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = PipelineResult(
            success=len(errors) == 0,
            data=current_data,
            errors=errors,
            metadata={
                "steps_executed": len(self.steps),
                "final_shape": current_data.shape if current_data is not None else None,
                "timestamp": datetime.now().isoformat()
            },
            execution_time=execution_time
        )
        
        self.history.append(result)
        logger.info(f"Pipeline completed in {execution_time:.2f}s with {len(errors)} errors")
        
        return result
    
    async def execute_with_validation(
        self, 
        data: pd.DataFrame, 
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        if validation_rules:
            validation_result = self._validate_input(data, validation_rules)
            if not validation_result['valid']:
                return PipelineResult(
                    success=False,
                    data=None,
                    errors=validation_result['errors'],
                    metadata={"validation_failed": True},
                    execution_time=0
                )
        
        return await self.execute(data)
    
    def _validate_input(self, data: pd.DataFrame, rules: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        
        if 'required_columns' in rules:
            missing = set(rules['required_columns']) - set(data.columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")
        
        if 'min_rows' in rules and len(data) < rules['min_rows']:
            errors.append(f"Insufficient rows: {len(data)} < {rules['min_rows']}")
        
        if 'max_null_percentage' in rules:
            null_percentage = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
            if null_percentage > rules['max_null_percentage']:
                errors.append(f"Too many null values: {null_percentage:.2%}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_history(self) -> List[Dict[str, Any]]:
        return [
            {
                "success": r.success,
                "errors": r.errors,
                "metadata": r.metadata,
                "execution_time": r.execution_time
            }
            for r in self.history
        ]
    
    def clear_history(self):
        self.history.clear()
