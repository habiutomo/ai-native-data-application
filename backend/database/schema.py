from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from loguru import logger

Base = declarative_base()

@dataclass
class ColumnDefinition:
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[Any] = None

class SchemaManager:
    def __init__(self):
        self.schemas: Dict[str, List[ColumnDefinition]] = {}
    
    def define_schema(self, table_name: str, columns: List[ColumnDefinition]) -> None:
        self.schemas[table_name] = columns
        logger.info(f"Defined schema for table {table_name} with {len(columns)} columns")
    
    def generate_sql(self, table_name: str) -> str:
        if table_name not in self.schemas:
            raise ValueError(f"Schema not defined for table {table_name}")
        
        columns = self.schemas[table_name]
        
        column_defs = []
        for col in columns:
            col_def = f"    {col.name} {self._map_type(col.type)}"
            
            if col.primary_key:
                col_def += " PRIMARY KEY"
            if not col.nullable and not col.primary_key:
                col_def += " NOT NULL"
            if col.foreign_key:
                col_def += f" REFERENCES {col.foreign_key}"
            if col.default is not None:
                col_def += f" DEFAULT {col.default}"
            
            column_defs.append(col_def)
        
        sql = f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(column_defs)
        sql += "\n);"
        
        return sql
    
    def validate_data(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if table_name not in self.schemas:
            return {"valid": False, "errors": ["Schema not defined"]}
        
        errors = []
        columns = self.schemas[table_name]
        
        for col in columns:
            if col.name in data:
                value = data[col.name]
                
                if not col.nullable and value is None:
                    errors.append(f"Column {col.name} cannot be null")
                
                if col.type == "integer" and value is not None:
                    if not isinstance(value, int):
                        errors.append(f"Column {col.name} must be an integer")
                
                elif col.type == "float" and value is not None:
                    if not isinstance(value, (int, float)):
                        errors.append(f"Column {col.name} must be a number")
                
                elif col.type == "string" and value is not None:
                    if not isinstance(value, str):
                        errors.append(f"Column {col.name} must be a string")
            
            elif not col.nullable and col.default is None:
                errors.append(f"Required column {col.name} is missing")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def generate_migration(self, old_table: str, new_table: str) -> str:
        old_cols = set(self.schemas.get(old_table, []))
        new_cols = set(self.schemas.get(new_table, []))
        
        added = new_cols - old_cols
        removed = old_cols - new_cols
        
        migration = f"-- Migration for table {old_table}\n"
        
        for col in added:
            migration += f"ALTER TABLE {old_table} ADD COLUMN {col.name} {self._map_type(col.type)};\n"
        
        for col in removed:
            migration += f"ALTER TABLE {old_table} DROP COLUMN {col.name};\n"
        
        return migration
    
    def _map_type(self, type_str: str) -> str:
        type_mapping = {
            "integer": "INTEGER",
            "int": "INTEGER",
            "float": "FLOAT",
            "decimal": "DECIMAL(10,2)",
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "boolean": "BOOLEAN",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "json": "JSON"
        }
        return type_mapping.get(type_str.lower(), "VARCHAR(255)")
    
    def export_schema(self, table_name: str) -> Dict[str, Any]:
        if table_name not in self.schemas:
            return {}
        
        columns = self.schemas[table_name]
        return {
            "table_name": table_name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.type,
                    "nullable": col.nullable,
                    "primary_key": col.primary_key,
                    "foreign_key": col.foreign_key,
                    "default": col.default
                }
                for col in columns
            ]
        }
    
    def import_schema(self, schema_data: Dict[str, Any]) -> None:
        table_name = schema_data["table_name"]
        columns = [
            ColumnDefinition(**col_data)
            for col_data in schema_data["columns"]
        ]
        self.define_schema(table_name, columns)
