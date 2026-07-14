import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from loguru import logger

from backend.ai.ollama_client import OllamaClient

class DataEnricher:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.enrichment_rules: Dict[str, Callable] = {}
    
    async def enrich(
        self, 
        data: pd.DataFrame, 
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        logger.info(f"Enriching dataframe with {len(data)} rows")
        
        enriched_data = data.copy()
        
        if rules:
            for rule in rules:
                enriched_data = await self._apply_rule(enriched_data, rule)
        else:
            enriched_data = await self._auto_enrich(enriched_data)
        
        return enriched_data
    
    async def _apply_rule(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        rule_type = rule.get('type')
        
        if rule_type == 'fill_missing':
            return self._fill_missing(data, rule)
        elif rule_type == 'transform':
            return await self._transform_column(data, rule)
        elif rule_type == 'extract_features':
            return self._extract_features(data, rule)
        elif rule_type == 'categorize':
            return await self._categorize_column(data, rule)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return data
    
    def _fill_missing(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        column = rule.get('column')
        method = rule.get('method', 'mean')
        
        if column not in data.columns:
            return data
        
        if method == 'mean':
            data[column] = data[column].fillna(data[column].mean())
        elif method == 'median':
            data[column] = data[column].fillna(data[column].median())
        elif method == 'mode':
            mode_value = data[column].mode()[0] if not data[column].mode().empty else None
            data[column] = data[column].fillna(mode_value)
        elif method == 'forward_fill':
            data[column] = data[column].ffill()
        elif method == 'backward_fill':
            data[column] = data[column].bfill()
        
        return data
    
    async def _transform_column(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        column = rule.get('column')
        transformation = rule.get('transformation')
        
        if column not in data.columns:
            return data
        
        if transformation == 'normalize':
            min_val = data[column].min()
            max_val = data[column].max()
            if max_val - min_val > 0:
                data[column] = (data[column] - min_val) / (max_val - min_val)
        elif transformation == 'standardize':
            mean_val = data[column].mean()
            std_val = data[column].std()
            if std_val > 0:
                data[column] = (data[column] - mean_val) / std_val
        elif transformation == 'log':
            data[column] = np.log1p(data[column])
        elif transformation == 'categorical_to_numeric':
            data[column] = data[column].astype('category').cat.codes
        
        return data
    
    def _extract_features(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        source_column = rule.get('source_column')
        features = rule.get('features', [])
        
        if source_column not in data.columns:
            return data
        
        for feature in features:
            if feature == 'day_of_week' and pd.api.types.is_datetime64_any_dtype(data[source_column]):
                data[f'{source_column}_day_of_week'] = data[source_column].dt.dayofweek
            elif feature == 'month' and pd.api.types.is_datetime64_any_dtype(data[source_column]):
                data[f'{source_column}_month'] = data[source_column].dt.month
            elif feature == 'year' and pd.api.types.is_datetime64_any_dtype(data[source_column]):
                data[f'{source_column}_year'] = data[source_column].dt.year
            elif feature == 'length' and data[source_column].dtype == 'object':
                data[f'{source_column}_length'] = data[source_column].str.len()
            elif feature == 'is_weekend' and pd.api.types.is_datetime64_any_dtype(data[source_column]):
                data[f'{source_column}_is_weekend'] = data[source_column].dt.dayofweek >= 5
        
        return data
    
    async def _categorize_column(self, data: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
        column = rule.get('column')
        categories = rule.get('categories', {})
        
        if column not in data.columns:
            return data
        
        if categories:
            data[f'{column}_category'] = data[column].map(categories)
        else:
            prompt = f"Generate categories for the following unique values:\n{data[column].unique()[:20].tolist()}"
            response = await self.ollama_client.generate(prompt)
            
            try:
                import json
                category_mapping = json.loads(response)
                data[f'{column}_category'] = data[column].map(category_mapping)
            except:
                data[f'{column}_category'] = data[column].astype('category').cat.codes
        
        return data
    
    async def _auto_enrich(self, data: pd.DataFrame) -> pd.DataFrame:
        enriched_data = data.copy()
        
        for column in data.columns:
            if data[column].isnull().any():
                if pd.api.types.is_numeric_dtype(data[column]):
                    enriched_data = self._fill_missing(
                        enriched_data, 
                        {'column': column, 'method': 'median'}
                    )
                else:
                    enriched_data = self._fill_missing(
                        enriched_data, 
                        {'column': column, 'method': 'mode'}
                    )
        
        datetime_cols = data.select_dtypes(include=['datetime64']).columns
        for col in datetime_cols:
            enriched_data = self._extract_features(
                enriched_data, 
                {'source_column': col, 'features': ['day_of_week', 'month', 'year', 'is_weekend']}
            )
        
        return enriched_data
