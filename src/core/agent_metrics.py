"""
性能指标收集和监控模块
用于收集 LLM 调用、工具执行、命令执行等性能数据
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, ContextManager
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: datetime
    operation_type: str  # 'llm_call', 'tool_call', 'command_exec', 'file_op'
    operation_name: str
    duration_ms: float
    success: bool = True
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class SessionStats:
    """会话统计信息"""
    start_time: datetime = field(default_factory=datetime.now)
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration_ms: float = 0.0
    total_tokens: Dict[str, int] = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    })
    llm_calls: int = 0
    tool_calls: int = 0
    command_executions: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    @property
    def average_duration_ms(self) -> float:
        """平均执行时间"""
        if self.total_operations == 0:
            return 0.0
        return self.total_duration_ms / self.total_operations
    
    @property
    def session_duration_minutes(self) -> float:
        """会话持续时间（分钟）"""
        return (datetime.now() - self.start_time).total_seconds() / 60


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, buffer_size: int = 1000, auto_export: bool = True):
        self.buffer_size = buffer_size
        self.auto_export = auto_export
        self.metrics_buffer: List[PerformanceMetrics] = []
        self.session_stats = SessionStats()
        self._lock = threading.Lock()
        
        # 导出配置
        self.export_file = Path("performance_metrics.json")
        self.last_export_time = datetime.now()
        self.export_interval = timedelta(hours=1)  # 每小时导出一次
    
    @contextmanager
    def measure_operation(self, op_type: str, op_name: str, **kwargs) -> ContextManager[Dict]:
        """
        性能测量上下文管理器
        
        Args:
            op_type: 操作类型 ('llm_call', 'tool_call', 'command_exec', 'file_op')
            op_name: 操作名称
            **kwargs: 额外数据
        
        Usage:
            with metrics.measure_operation("llm_call", "kimi-k2") as ctx:
                result = llm.invoke(messages)
                ctx["token_usage"] = extract_token_usage(result)
        """
        start_time = time.time()
        context = {"additional_data": kwargs}
        
        try:
            yield context
            # 成功完成
            duration = (time.time() - start_time) * 1000
            self._record_metric(
                op_type=op_type,
                op_name=op_name,
                duration_ms=duration,
                success=True,
                token_usage=context.get("token_usage"),
                additional_data=context.get("additional_data")
            )
        except Exception as e:
            # 执行失败
            duration = (time.time() - start_time) * 1000
            self._record_metric(
                op_type=op_type,
                op_name=op_name,
                duration_ms=duration,
                success=False,
                error_message=str(e),
                additional_data=context.get("additional_data")
            )
            raise
    
    def _record_metric(self, op_type: str, op_name: str, duration_ms: float, 
                      success: bool, error_message: Optional[str] = None,
                      token_usage: Optional[Dict[str, int]] = None,
                      additional_data: Optional[Dict[str, Any]] = None):
        """记录性能指标"""
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            operation_type=op_type,
            operation_name=op_name,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            token_usage=token_usage,
            additional_data=additional_data
        )
        
        with self._lock:
            # 添加到缓冲区
            self.metrics_buffer.append(metric)
            
            # 更新会话统计
            self._update_session_stats(metric)
            
            # 检查缓冲区大小
            if len(self.metrics_buffer) > self.buffer_size:
                self.metrics_buffer = self.metrics_buffer[-self.buffer_size:]
            
            # 检查是否需要导出
            if self.auto_export and self._should_export():
                self._export_metrics()
    
    def _update_session_stats(self, metric: PerformanceMetrics):
        """更新会话统计信息"""
        self.session_stats.total_operations += 1
        self.session_stats.total_duration_ms += metric.duration_ms
        
        if metric.success:
            self.session_stats.successful_operations += 1
        else:
            self.session_stats.failed_operations += 1
        
        # 按操作类型统计
        if metric.operation_type == "llm_call":
            self.session_stats.llm_calls += 1
            # 更新 Token 统计
            if metric.token_usage:
                for key, value in metric.token_usage.items():
                    if key in self.session_stats.total_tokens:
                        self.session_stats.total_tokens[key] += value
        elif metric.operation_type == "tool_call":
            self.session_stats.tool_calls += 1
        elif metric.operation_type == "command_exec":
            self.session_stats.command_executions += 1
    
    def _should_export(self) -> bool:
        """检查是否应该导出指标"""
        return datetime.now() - self.last_export_time > self.export_interval
    
    def _export_metrics(self):
        """导出指标到文件"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "session_stats": asdict(self.session_stats),
                "recent_metrics": [asdict(m) for m in self.metrics_buffer[-100:]]  # 最近100条
            }
            
            with open(self.export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.last_export_time = datetime.now()
        except Exception as e:
            print(f"⚠️ 导出性能指标失败: {e}")
    
    def get_session_stats(self) -> SessionStats:
        """获取当前会话统计"""
        with self._lock:
            return self.session_stats
    
    def get_recent_metrics(self, count: int = 50) -> List[PerformanceMetrics]:
        """获取最近的性能指标"""
        with self._lock:
            return self.metrics_buffer[-count:] if self.metrics_buffer else []
    
    def get_operation_stats(self, op_type: Optional[str] = None) -> Dict[str, Any]:
        """获取操作统计信息"""
        with self._lock:
            metrics = self.metrics_buffer
            if op_type:
                metrics = [m for m in metrics if m.operation_type == op_type]
            
            if not metrics:
                return {"count": 0, "success_rate": 0.0, "avg_duration_ms": 0.0}
            
            successful = sum(1 for m in metrics if m.success)
            total_duration = sum(m.duration_ms for m in metrics)
            
            return {
                "count": len(metrics),
                "success_rate": successful / len(metrics),
                "avg_duration_ms": total_duration / len(metrics),
                "total_duration_ms": total_duration,
                "successful_operations": successful,
                "failed_operations": len(metrics) - successful
            }
    
    def get_token_usage_summary(self) -> Dict[str, int]:
        """获取 Token 使用汇总"""
        with self._lock:
            return self.session_stats.total_tokens.copy()
    
    def reset_session_stats(self):
        """重置会话统计"""
        with self._lock:
            self.session_stats = SessionStats()
            self.metrics_buffer.clear()
    
    def format_stats_report(self) -> str:
        """格式化统计报告"""
        stats = self.get_session_stats()
        
        report = f"""
📊 性能统计报告
{'=' * 50}

⏱️  会话信息:
   持续时间: {stats.session_duration_minutes:.1f} 分钟
   开始时间: {stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}

🎯 操作统计:
   总操作数: {stats.total_operations}
   成功率: {stats.success_rate:.1%}
   平均耗时: {stats.average_duration_ms:.1f}ms

🔧 操作分类:
   LLM 调用: {stats.llm_calls}
   工具调用: {stats.tool_calls}
   命令执行: {stats.command_executions}

🪙 Token 使用:
   输入 Token: {stats.total_tokens['prompt_tokens']:,}
   输出 Token: {stats.total_tokens['completion_tokens']:,}
   总计 Token: {stats.total_tokens['total_tokens']:,}

📈 性能指标:
   总耗时: {stats.total_duration_ms:.1f}ms
   成功操作: {stats.successful_operations}
   失败操作: {stats.failed_operations}
"""
        return report


# 全局指标收集器实例
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    return metrics_collector


# 便捷装饰器
def measure_performance(op_type: str, op_name: str = None):
    """性能测量装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = op_name or func.__name__
            with metrics_collector.measure_operation(op_type, name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
