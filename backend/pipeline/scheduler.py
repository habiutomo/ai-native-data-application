from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from loguru import logger

class ScheduleFrequency(Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class ScheduledTask:
    task_id: str
    name: str
    function: Callable
    frequency: ScheduleFrequency
    params: Dict[str, Any]
    next_run: datetime
    last_run: Optional[datetime] = None
    enabled: bool = True

class PipelineScheduler:
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.execution_log: List[Dict[str, Any]] = []
    
    def schedule(
        self, 
        task_id: str,
        name: str,
        function: Callable,
        frequency: ScheduleFrequency,
        params: Dict[str, Any] = None,
        start_time: Optional[datetime] = None
    ) -> ScheduledTask:
        if start_time is None:
            start_time = datetime.now()
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            function=function,
            frequency=frequency,
            params=params or {},
            next_run=start_time
        )
        
        self.tasks[task_id] = task
        logger.info(f"Scheduled task {name} with frequency {frequency.value}")
        
        return task
    
    def unschedule(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Unscheduled task {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            return True
        return False
    
    async def run_task(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found"}
        
        task = self.tasks[task_id]
        
        try:
            logger.info(f"Running task: {task.name}")
            
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function(**task.params)
            else:
                result = task.function(**task.params)
            
            task.last_run = datetime.now()
            task.next_run = self._calculate_next_run(task.frequency)
            
            log_entry = {
                "task_id": task_id,
                "name": task.name,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "result": str(result)[:500]
            }
            self.execution_log.append(log_entry)
            
            logger.info(f"Task {task.name} completed successfully")
            return {"status": "success", "result": result}
            
        except Exception as e:
            error_msg = f"Task {task.name} failed: {str(e)}"
            logger.error(error_msg)
            
            log_entry = {
                "task_id": task_id,
                "name": task.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
            self.execution_log.append(log_entry)
            
            return {"status": "failed", "error": str(e)}
    
    async def start(self):
        self.running = True
        logger.info("Scheduler started")
        
        while self.running:
            now = datetime.now()
            
            for task_id, task in self.tasks.items():
                if task.enabled and now >= task.next_run:
                    await self.run_task(task_id)
            
            await asyncio.sleep(1)
    
    def stop(self):
        self.running = False
        logger.info("Scheduler stopped")
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "frequency": t.frequency.value,
                "enabled": t.enabled,
                "next_run": t.next_run.isoformat(),
                "last_run": t.last_run.isoformat() if t.last_run else None
            }
            for t in self.tasks.values()
        ]
    
    def get_execution_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.execution_log[-limit:]
    
    def _calculate_next_run(self, frequency: ScheduleFrequency) -> datetime:
        now = datetime.now()
        
        if frequency == ScheduleFrequency.ONCE:
            return now + timedelta(hours=24)
        elif frequency == ScheduleFrequency.HOURLY:
            return now + timedelta(hours=1)
        elif frequency == ScheduleFrequency.DAILY:
            return now + timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif frequency == ScheduleFrequency.MONTHLY:
            return now + timedelta(days=30)
        else:
            return now + timedelta(hours=1)
