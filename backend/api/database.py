from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.core.database import get_db
from backend.database.manager import DatabaseManager
from backend.database.optimizer import QueryOptimizer
from backend.database.schema import SchemaManager, ColumnDefinition

router = APIRouter()
db_manager = DatabaseManager()
query_optimizer = QueryOptimizer()
schema_manager = SchemaManager()

@router.get("/tables")
async def list_tables():
    tables = await db_manager.list_tables()
    return {"tables": tables}

@router.get("/tables/{table_name}")
async def get_table_info(table_name: str):
    try:
        info = await db_manager.get_table_info(table_name)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {e}")

@router.get("/stats")
async def get_database_stats():
    stats = await db_manager.get_database_stats()
    return stats

@router.post("/query")
async def execute_query(query: str):
    try:
        result = await db_manager.execute_query(query)
        return {
            "columns": result.columns.tolist(),
            "data": result.to_dict('records'),
            "row_count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/optimize")
async def optimize_query(query: str):
    result = await query_optimizer.optimize_query(query)
    return result

@router.post("/explain")
async def explain_query(query: str):
    result = await query_optimizer.explain_query(query)
    return result

@router.post("/analyze-query")
async def analyze_query(query: str):
    result = await query_optimizer.analyze_query(query)
    return result

@router.post("/suggest-indexes/{table_name}")
async def suggest_indexes(table_name: str):
    try:
        info = await db_manager.get_table_info(table_name)
        suggestions = await query_optimizer.suggest_indexes(info)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/schema/define")
async def define_schema(table_name: str, columns: List[Dict[str, Any]]):
    col_definitions = [ColumnDefinition(**col) for col in columns]
    schema_manager.define_schema(table_name, col_definitions)
    return {"message": f"Schema defined for table {table_name}"}

@router.get("/schema/{table_name}/sql")
async def get_schema_sql(table_name: str):
    try:
        sql = schema_manager.generate_sql(table_name)
        return {"sql": sql}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/schema/validate")
async def validate_data(table_name: str, data: Dict[str, Any]):
    result = schema_manager.validate_data(table_name, data)
    return result

@router.post("/create-table")
async def create_table_from_dataframe(
    table_name: str,
    data: List[Dict[str, Any]]
):
    df = pd.DataFrame(data)
    success = await db_manager.create_table_from_dataframe(df, table_name)
    
    if success:
        return {"message": f"Table {table_name} created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create table")

@router.post("/backup/{table_name}")
async def backup_table(table_name: str):
    try:
        df = await db_manager.backup_table(table_name)
        return {
            "table": table_name,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/query-history")
async def get_query_history(limit: int = 50):
    history = query_optimizer.get_query_history(limit)
    return {"history": history}
