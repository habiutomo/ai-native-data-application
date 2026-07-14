from openai import AsyncOpenAI
from typing import Optional
from loguru import logger

from backend.core.config import settings

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system", 
                    "content": "You are a data analyst AI. Provide clear, actionable insights."
                })
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def analyze_code(self, code: str) -> str:
        system_prompt = """You are a code analysis AI. Analyze the provided code and suggest improvements, optimizations, or fixes."""
        
        prompt = f"Analyze this code and provide suggestions:\n\n```python\n{code}\n```"
        
        return await self.generate(prompt, system_prompt)
    
    async def generate_query(self, description: str, schema: str) -> str:
        system_prompt = """You are a SQL expert. Generate optimized SQL queries based on the description and schema provided."""
        
        prompt = f"""Generate a SQL query for this requirement:

Description: {description}

Database Schema:
{schema}

Provide the optimized SQL query:"""
        
        return await self.generate(prompt, system_prompt)
