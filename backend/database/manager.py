import pandas as pd
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from loguru import logger

from backend.core.config import settings
from backend.ai.ollama_client import OllamaClient

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.inspector = inspect(self.engine)
        self.ollama_client = OllamaClient()
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        columns = self.inspector.get_columns(table_name)
        pk = self.inspector.get_pk_constraint(table_name)
        fk = self.inspector.get_foreign_keys(table_name)
        indexes = self.inspector.get_indexes(table_name)
        
        return {
            "name": table_name,
            "columns": [
                {
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col.get('nullable', True),
                    "default": str(col.get('default')) if col.get('default') else None
                }
                for col in columns
            ],
            "primary_key": pk,
            "foreign_keys": fk,
            "indexes": [
                {
                    "name": idx['name'],
                    "columns": idx['column_names'],
                    "unique": idx.get('unique', False)
                }
                for idx in indexes
            ]
        }
    
    async def list_tables(self) -> List[str]:
        return self.inspector.get_table_names()
    
    async def get_database_stats(self) -> Dict[str, Any]:
        tables = await self.list_tables()
        stats = {
            "total_tables": len(tables),
            "tables": {}
        }
        
        for table in tables:
            try:
                info = await self.get_table_info(table)
                row_count = await self._get_row_count(table)
                stats["tables"][table] = {
                    "columns": len(info["columns"]),
                    "rows": row_count,
                    "has_indexes": len(info["indexes"]) > 0
                }
            except Exception as e:
                logger.warning(f"Could not get stats for table {table}: {e}")
        
        return stats
    
    async def _get_row_count(self, table_name: str) -> int:
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = await self.execute_query(query)
        return result.iloc[0, 0] if not result.empty else 0
    
    async def generate_sample_data(
        self, 
        table_name: str, 
        rows: int = 100
    ) -> pd.DataFrame:
        info = await self.get_table_info(table_name)
        
        sample_query = f"SELECT * FROM {table_name} LIMIT {rows}"
        return await self.execute_query(sample_query)
    
    async def backup_table(self, table_name: str) -> pd.DataFrame:
        logger.info(f"Backing up table: {table_name}")
        return await self.execute_query(f"SELECT * FROM {table_name}")
    
    async def create_table_from_dataframe(
        self, 
        df: pd.DataFrame, 
        table_name: str
    ) -> bool:
        try:
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            logger.info(f"Created table {table_name} from DataFrame")
            return True
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            return False
    
    async def suggest_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        info = await self.get_table_info(table_name)
        
        prompt = f"""Analyze this database table and suggest useful indexes:

Table: {table_name}
Columns: {[col['name'] for col in info['columns']]}
Existing Indexes: {info['indexes']}

Provide index suggestions with reasoning."""
        
        response = await self.ollama_client.generate(prompt)
        
        return {"table": table_name, "suggestions": response}
