import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

from backend.ai.ollama_client import OllamaClient

@dataclass
class AnalysisResult:
    summary: str
    insights: List[str]
    statistics: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]

class DataAnalyzer:
    def __init__(self):
        self.ollama_client = OllamaClient()
    
    async def analyze(self, data: pd.DataFrame, context: Optional[str] = None) -> AnalysisResult:
        logger.info(f"Starting analysis on dataframe with shape {data.shape}")
        
        statistics = self._calculate_statistics(data)
        anomalies = self._detect_anomalies(data)
        
        prompt = self._build_analysis_prompt(data, statistics, anomalies, context)
        ai_analysis = await self.ollama_client.generate(prompt)
        
        summary = self._extract_summary(ai_analysis)
        insights = self._extract_insights(ai_analysis)
        visualizations = self._suggest_visualizations(data, statistics)
        
        return AnalysisResult(
            summary=summary,
            insights=insights,
            statistics=statistics,
            visualizations=visualizations,
            anomalies=anomalies
        )
    
    def _calculate_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        stats = {
            "rows": len(data),
            "columns": len(data.columns),
            "numeric_columns": data.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": data.select_dtypes(include=['object', 'category']).columns.tolist(),
            "missing_values": data.isnull().sum().to_dict(),
            "memory_usage": data.memory_usage(deep=True).sum()
        }
        
        numeric_stats = data.describe().to_dict()
        stats["numeric_summary"] = numeric_stats
        
        return stats
    
    def _detect_anomalies(self, data: pd.DataFrame, threshold: float = 3.0) -> List[Dict[str, Any]]:
        anomalies = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) > 0:
                mean = col_data.mean()
                std = col_data.std()
                if std > 0:
                    z_scores = np.abs((col_data - mean) / std)
                    anomaly_mask = z_scores > threshold
                    if anomaly_mask.any():
                        anomalies.append({
                            "column": col,
                            "count": int(anomaly_mask.sum()),
                            "indices": col_data[anomaly_mask].index.tolist()[:10]
                        })
        
        return anomalies
    
    def _build_analysis_prompt(
        self, 
        data: pd.DataFrame, 
        statistics: Dict, 
        anomalies: List, 
        context: Optional[str]
    ) -> str:
        sample_data = data.head(5).to_string()
        
        prompt = f"""Analyze the following dataset and provide insights:

Dataset Overview:
- Rows: {statistics['rows']}
- Columns: {statistics['columns']}
- Numeric columns: {statistics['numeric_columns']}
- Categorical columns: {statistics['categorical_columns']}

Sample Data:
{sample_data}

Anomalies Detected: {len(anomalies)}
"""
        
        if context:
            prompt += f"\nContext: {context}"
        
        prompt += """
Please provide:
1. A brief summary of the data
2. Key insights and patterns
3. Potential issues or areas of concern
4. Recommendations for further analysis
"""
        
        return prompt
    
    def _extract_summary(self, ai_response: str) -> str:
        lines = ai_response.split('\n')
        summary_lines = []
        capture = False
        
        for line in lines:
            if 'summary' in line.lower() or capture:
                capture = True
                if line.strip():
                    summary_lines.append(line)
                if len(summary_lines) >= 3:
                    break
        
        return '\n'.join(summary_lines) if summary_lines else ai_response[:500]
    
    def _extract_insights(self, ai_response: str) -> List[str]:
        insights = []
        lines = ai_response.split('\n')
        current_insight = ""
        
        for line in lines:
            if line.strip().startswith(('-', '*', '•')) or (line.strip().split('.')[0].isdigit()):
                if current_insight:
                    insights.append(current_insight.strip())
                current_insight = line.strip()
            elif current_insight:
                current_insight += " " + line.strip()
        
        if current_insight:
            insights.append(current_insight.strip())
        
        return insights[:10]
    
    def _suggest_visualizations(
        self, 
        data: pd.DataFrame, 
        statistics: Dict
    ) -> List[Dict[str, Any]]:
        visualizations = []
        
        numeric_cols = statistics.get('numeric_columns', [])
        categorical_cols = statistics.get('categorical_columns', [])
        
        if len(numeric_cols) >= 2:
            visualizations.append({
                "type": "scatter",
                "columns": numeric_cols[:2],
                "description": f"Scatter plot of {numeric_cols[0]} vs {numeric_cols[1]}"
            })
        
        if numeric_cols:
            visualizations.append({
                "type": "histogram",
                "columns": numeric_cols[:3],
                "description": f"Distribution of {', '.join(numeric_cols[:3])}"
            })
        
        if categorical_cols and numeric_cols:
            visualizations.append({
                "type": "bar",
                "columns": [categorical_cols[0], numeric_cols[0]],
                "description": f"{numeric_cols[0]} by {categorical_cols[0]}"
            })
        
        if len(numeric_cols) >= 3:
            visualizations.append({
                "type": "correlation_heatmap",
                "columns": numeric_cols[:5],
                "description": "Correlation matrix of numeric features"
            })
        
        return visualizations
