from typing import Dict, List, Any, Optional
from loguru import logger

from backend.ai.ollama_client import OllamaClient
from backend.core.database import get_db_context

class QueryOptimizer:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.query_history: List[Dict[str, Any]] = []
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        prompt = f"""Analyze this SQL query for performance issues and suggest optimizations:

Query:
```sql
{query}
```

Provide:
1. Query analysis (joins, subqueries, etc.)
2. Potential performance issues
3. Optimization suggestions
4. Index recommendations
"""
        
        analysis = await self.ollama_client.generate(prompt)
        
        result = {
            "original_query": query,
            "analysis": analysis,
            "timestamp": self._get_timestamp()
        }
        
        self.query_history.append(result)
        
        return result
    
    async def optimize_query(self, query: str) -> Dict[str, Any]:
        prompt = f"""Optimize this SQL query for better performance:

Original Query:
```sql
{query}
```

Provide:
1. Optimized query
2. Explanation of changes
3. Expected performance improvement
"""
        
        optimized = await self.ollama_client.generate(prompt)
        
        return {
            "original": query,
            "optimized": optimized,
            "timestamp": self._get_timestamp()
        }
    
    async def explain_query(self, query: str) -> Dict[str, Any]:
        try:
            with get_db_context() as db:
                explain_query = f"EXPLAIN ANALYZE {query}"
                result = db.execute(explain_query)
                plan = result.fetchall()
                
                prompt = f"""Explain this query execution plan:

{plan}

Provide a clear explanation of:
1. The query execution steps
2. Any full table scans
3. Join strategies used
4. Potential bottlenecks
"""
                
                explanation = await self.ollama_client.generate(prompt)
                
                return {
                    "query": query,
                    "execution_plan": str(plan),
                    "explanation": explanation
                }
                
        except Exception as e:
            logger.error(f"Could not explain query: {e}")
            return {"error": str(e)}
    
    async def suggest_indexes(self, schema_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        prompt = f"""Analyze this database schema and suggest indexes:

Schema:
{schema_info}

Provide index suggestions with:
1. Column(s) to index
2. Index type (B-tree, Hash, etc.)
3. Reasoning for the suggestion
"""
        
        suggestions = await self.ollama_client.generate(prompt)
        
        return {"suggestions": suggestions}
    
    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.query_history[-limit:]
    
    def clear_history(self):
        self.query_history.clear()
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
