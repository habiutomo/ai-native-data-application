import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from loguru import logger

class DataTransformer:
    def __init__(self):
        self.transformation_history: List[Dict[str, Any]] = []
    
    def transform(self, data: pd.DataFrame, transformations: List[Dict[str, Any]]) -> pd.DataFrame:
        result = data.copy()
        
        for transformation in transformations:
            operation = transformation.get('operation')
            params = transformation.get('params', {})
            
            try:
                if operation == 'rename':
                    result = self.rename_columns(result, params)
                elif operation == 'drop':
                    result = self.drop_columns(result, params)
                elif operation == 'filter':
                    result = self.filter_rows(result, params)
                elif operation == 'sort':
                    result = self.sort_data(result, params)
                elif operation == 'aggregate':
                    result = self.aggregate_data(result, params)
                elif operation == 'pivot':
                    result = self.pivot_data(result, params)
                elif operation == 'melt':
                    result = self.melt_data(result, params)
                elif operation == 'merge':
                    result = self.merge_data(result, params)
                elif operation == 'cast':
                    result = self.cast_types(result, params)
                else:
                    logger.warning(f"Unknown transformation: {operation}")
                
                self.transformation_history.append({
                    "operation": operation,
                    "params": params,
                    "result_shape": result.shape
                })
                
            except Exception as e:
                logger.error(f"Transformation error: {operation}: {e}")
                raise
        
        return result
    
    def rename_columns(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        mapping = params.get('mapping', {})
        return data.rename(columns=mapping)
    
    def drop_columns(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        columns = params.get('columns', [])
        return data.drop(columns=columns, errors='ignore')
    
    def filter_rows(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        condition = params.get('condition')
        if condition:
            return data.query(condition)
        return data
    
    def sort_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        by = params.get('by', [])
        ascending = params.get('ascending', True)
        return data.sort_values(by=by, ascending=ascending)
    
    def aggregate_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        group_by = params.get('group_by', [])
        agg_func = params.get('agg_func', 'mean')
        return data.groupby(group_by).agg(agg_func).reset_index()
    
    def pivot_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        index = params.get('index')
        columns = params.get('columns')
        values = params.get('values')
        agg_func = params.get('agg_func', 'sum')
        
        return data.pivot_table(
            index=index,
            columns=columns,
            values=values,
            aggfunc=agg_func
        ).reset_index()
    
    def melt_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        id_vars = params.get('id_vars', [])
        value_vars = params.get('value_vars', [])
        var_name = params.get('var_name', 'variable')
        value_name = params.get('value_name', 'value')
        
        return pd.melt(
            data,
            id_vars=id_vars,
            value_vars=value_vars,
            var_name=var_name,
            value_name=value_name
        )
    
    def merge_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        other = params.get('other')
        on = params.get('on')
        how = params.get('how', 'inner')
        
        if isinstance(other, pd.DataFrame):
            return data.merge(other, on=on, how=how)
        return data
    
    def cast_types(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        type_mapping = params.get('types', {})
        result = data.copy()
        
        for column, dtype in type_mapping.items():
            if column in result.columns:
                try:
                    if dtype == 'datetime':
                        result[column] = pd.to_datetime(result[column])
                    elif dtype == 'numeric':
                        result[column] = pd.to_numeric(result[column], errors='coerce')
                    elif dtype == 'category':
                        result[column] = result[column].astype('category')
                    else:
                        result[column] = result[column].astype(dtype)
                except Exception as e:
                    logger.warning(f"Could not cast {column} to {dtype}: {e}")
        
        return result
    
    def clean_column_names(self, data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        result.columns = result.columns.str.lower()
        result.columns = result.columns.str.replace(' ', '_')
        result.columns = result.columns.str.replace('[^a-zA-Z0-9_]', '', regex=True)
        return result
    
    def remove_duplicates(self, data: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        return data.drop_duplicates(subset=subset)
    
    def handle_missing_values(
        self, 
        data: pd.DataFrame, 
        strategy: str = 'auto',
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        result = data.copy()
        target_columns = columns or result.columns.tolist()
        
        for col in target_columns:
            if col not in result.columns:
                continue
            
            if strategy == 'auto':
                if result[col].dtype in ['int64', 'float64']:
                    result[col] = result[col].fillna(result[col].median())
                else:
                    mode = result[col].mode()
                    if not mode.empty:
                        result[col] = result[col].fillna(mode[0])
            elif strategy == 'mean':
                result[col] = result[col].fillna(result[col].mean())
            elif strategy == 'median':
                result[col] = result[col].fillna(result[col].median())
            elif strategy == 'mode':
                mode = result[col].mode()
                if not mode.empty:
                    result[col] = result[col].fillna(mode[0])
            elif strategy == 'drop':
                result = result.dropna(subset=[col])
        
        return result
