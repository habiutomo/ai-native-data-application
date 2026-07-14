import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from loguru import logger

from backend.ai.ollama_client import OllamaClient

class DataPredictor:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.models: Dict[str, Any] = {}
    
    async def predict(
        self, 
        data: pd.DataFrame, 
        target_column: str,
        task_type: str = "auto"
    ) -> Dict[str, Any]:
        logger.info(f"Building prediction model for column: {target_column}")
        
        if task_type == "auto":
            task_type = self._determine_task_type(data[target_column])
        
        X, y = self._prepare_features(data, target_column)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        if task_type == "classification":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            metric = accuracy_score(y_test, y_pred)
            metric_name = "accuracy"
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            metric = r2_score(y_test, y_pred)
            metric_name = "r2_score"
        
        feature_importance = self._get_feature_importance(model, X.columns.tolist())
        
        prompt = self._build_prediction_prompt(
            task_type, target_column, feature_importance, metric, metric_name
        )
        ai_insights = await self.ollama_client.generate(prompt)
        
        self.models[target_column] = model
        
        return {
            "task_type": task_type,
            "target_column": target_column,
            "metric_name": metric_name,
            "metric_value": metric,
            "feature_importance": feature_importance,
            "ai_insights": ai_insights,
            "model_type": type(model).__name__
        }
    
    async def forecast(
        self, 
        data: pd.DataFrame, 
        date_column: str, 
        value_column: str,
        periods: int = 30
    ) -> Dict[str, Any]:
        logger.info(f"Forecasting {periods} periods for column: {value_column}")
        
        ts_data = data[[date_column, value_column]].copy()
        ts_data[date_column] = pd.to_datetime(ts_data[date_column])
        ts_data = ts_data.sort_values(date_column)
        ts_data = ts_data.set_index(date_column)
        
        ts_data['day_of_week'] = ts_data.index.dayofweek
        ts_data['month'] = ts_data.index.month
        ts_data['day'] = ts_data.index.day
        
        X = ts_data[['day_of_week', 'month', 'day']]
        y = ts_data[value_column]
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        last_date = ts_data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=periods,
            freq='D'
        )
        
        future_df = pd.DataFrame({
            'day_of_week': future_dates.dayofweek,
            'month': future_dates.month,
            'day': future_dates.day
        }, index=future_dates)
        
        predictions = model.predict(future_df)
        
        forecast_df = pd.DataFrame({
            'date': future_dates,
            'predicted_value': predictions
        })
        
        prompt = f"""Analyze this time series forecast:
Target: {value_column}
Periods forecasted: {periods}
Trend: {'Increasing' if predictions[-1] > predictions[0] else 'Decreasing'}
Range: {predictions.min():.2f} to {predictions.max():.2f}

Provide insights about the forecast pattern and any recommendations."""
        
        ai_insights = await self.ollama_client.generate(prompt)
        
        return {
            "forecast": forecast_df.to_dict('records'),
            "historical_data": ts_data[value_column].tail(30).to_dict(),
            "ai_insights": ai_insights
        }
    
    def _determine_task_type(self, target: pd.Series) -> str:
        if target.dtype == 'object' or target.nunique() < 20:
            return "classification"
        return "regression"
    
    def _prepare_features(
        self, 
        data: pd.DataFrame, 
        target_column: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        X = data.drop(columns=[target_column])
        y = data[target_column]
        
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns
        
        X = X[numeric_cols]
        
        for col in categorical_cols:
            dummies = pd.get_dummies(data[col], prefix=col, drop_first=True)
            X = pd.concat([X, dummies], axis=1)
        
        X = X.fillna(0)
        
        return X, y
    
    def _get_feature_importance(
        self, 
        model: Any, 
        feature_names: List[str]
    ) -> Dict[str, float]:
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            return dict(zip(feature_names, importance.tolist()))
        return {}
    
    def _build_prediction_prompt(
        self, 
        task_type: str, 
        target_column: str, 
        feature_importance: Dict[str, float],
        metric: float,
        metric_name: str
    ) -> str:
        top_features = sorted(
            feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return f"""Analyze this prediction model:

Task Type: {task_type}
Target Column: {target_column}
Model Performance ({metric_name}): {metric:.4f}

Top Features:
{chr(10).join([f"- {f}: {v:.4f}" for f, v in top_features])}

Please provide:
1. Model performance assessment
2. Key predictive factors
3. Potential improvements
4. Business recommendations
"""
