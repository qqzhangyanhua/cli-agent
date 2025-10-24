"""
系统韧性管理模块
提供错误处理、重试机制、熔断器和降级策略
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import asyncio
import random


class ErrorType(Enum):
    """错误类型枚举"""
    LLM_CALL_FAILED = "llm_call_failed"
    TOOL_CALL_FAILED = "tool_call_failed"
    COMMAND_EXEC_FAILED = "command_exec_failed"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class FallbackStrategy(Enum):
    """降级策略枚举"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    SWITCH_MODEL = "switch_model"
    USE_TEMPLATE = "use_template"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    error_type: ErrorType
    error_message: str
    node_name: str
    user_input: str
    operation_name: str
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class RetryPolicy:
    """重试策略配置"""
    max_attempts: int = 3
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动


@dataclass
class CircuitBreakerState:
    """熔断器状态"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: int = 60  # 秒


@dataclass
class FallbackResult:
    """降级结果"""
    success: bool
    response: str
    strategy_used: FallbackStrategy
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class ResilienceManager:
    """系统韧性管理器"""
    
    def __init__(self):
        self.error_handlers: Dict[ErrorType, List[Callable]] = {}
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self.fallback_strategies: Dict[str, List[FallbackStrategy]] = {}
        self._lock = threading.Lock()
        
        # 默认配置
        self._setup_default_policies()
        
        # 错误统计
        self.error_stats: Dict[str, int] = {}
        self.recovery_stats: Dict[str, int] = {}
    
    def _setup_default_policies(self):
        """设置默认策略"""
        # 默认重试策略
        self.retry_policies["llm_call"] = RetryPolicy(max_attempts=3, base_delay=1.0)
        self.retry_policies["tool_call"] = RetryPolicy(max_attempts=2, base_delay=0.5)
        self.retry_policies["command_exec"] = RetryPolicy(max_attempts=1, base_delay=0.0)
        
        # 默认降级策略
        self.fallback_strategies["llm_call"] = [
            FallbackStrategy.RETRY_WITH_BACKOFF,
            FallbackStrategy.SWITCH_MODEL,
            FallbackStrategy.USE_TEMPLATE,
            FallbackStrategy.GRACEFUL_DEGRADATION
        ]
        
        self.fallback_strategies["tool_call"] = [
            FallbackStrategy.RETRY_WITH_BACKOFF,
            FallbackStrategy.GRACEFUL_DEGRADATION
        ]
        
        self.fallback_strategies["command_exec"] = [
            FallbackStrategy.GRACEFUL_DEGRADATION
        ]
    
    def register_error_handler(self, error_type: ErrorType, handler: Callable):
        """注册错误处理器"""
        if error_type not in self.error_handlers:
            self.error_handlers[error_type] = []
        self.error_handlers[error_type].append(handler)
    
    def handle_error(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """
        统一错误处理入口
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            降级处理结果
        """
        with self._lock:
            # 记录错误
            self._record_error(error, context)
            
            # 检查熔断器
            if self._is_circuit_open(context.operation_name):
                return self._circuit_breaker_response(context)
            
            # 获取降级策略
            strategies = self.fallback_strategies.get(
                context.operation_name, 
                [FallbackStrategy.GRACEFUL_DEGRADATION]
            )
            
            # 依次尝试降级策略
            for strategy in strategies:
                try:
                    result = self._execute_strategy(strategy, error, context)
                    if result.success:
                        # 记录成功恢复
                        self._record_recovery(context.operation_name, strategy)
                        return result
                except Exception as e:
                    print(f"⚠️ 降级策略 {strategy.value} 执行失败: {e}")
                    continue
            
            # 所有策略都失败，返回最终降级
            return self._final_fallback(error, context)
    
    def _record_error(self, error: Exception, context: ErrorContext):
        """记录错误信息"""
        error_key = f"{context.operation_name}:{context.error_type.value}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1
        
        # 更新熔断器状态
        self._update_circuit_breaker(context.operation_name, failed=True)
        
        print(f"🚨 错误记录: {context.operation_name} - {context.error_message}")
    
    def _record_recovery(self, operation_name: str, strategy: FallbackStrategy):
        """记录成功恢复"""
        recovery_key = f"{operation_name}:{strategy.value}"
        self.recovery_stats[recovery_key] = self.recovery_stats.get(recovery_key, 0) + 1
        
        # 重置熔断器
        self._update_circuit_breaker(operation_name, failed=False)
        
        print(f"✅ 恢复成功: {operation_name} 使用策略 {strategy.value}")
    
    def _is_circuit_open(self, operation_name: str) -> bool:
        """检查熔断器是否打开"""
        if operation_name not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[operation_name]
        
        if breaker.state == "OPEN":
            # 检查是否可以尝试恢复
            if breaker.last_failure_time:
                time_since_failure = (datetime.now() - breaker.last_failure_time).total_seconds()
                if time_since_failure > breaker.recovery_timeout:
                    breaker.state = "HALF_OPEN"
                    return False
            return True
        
        return False
    
    def _update_circuit_breaker(self, operation_name: str, failed: bool):
        """更新熔断器状态"""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreakerState()
        
        breaker = self.circuit_breakers[operation_name]
        
        if failed:
            breaker.failure_count += 1
            breaker.last_failure_time = datetime.now()
            
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = "OPEN"
                print(f"🔴 熔断器打开: {operation_name} (失败次数: {breaker.failure_count})")
        else:
            # 成功调用，重置计数器
            breaker.failure_count = 0
            breaker.state = "CLOSED"
    
    def _circuit_breaker_response(self, context: ErrorContext) -> FallbackResult:
        """熔断器响应"""
        return FallbackResult(
            success=False,
            response=f"🔴 服务暂时不可用，请稍后重试。操作: {context.operation_name}",
            strategy_used=FallbackStrategy.CIRCUIT_BREAKER,
            error_message="Circuit breaker is open"
        )
    
    def _execute_strategy(self, strategy: FallbackStrategy, error: Exception, 
                         context: ErrorContext) -> FallbackResult:
        """执行降级策略"""
        if strategy == FallbackStrategy.RETRY_WITH_BACKOFF:
            return self._retry_with_backoff(error, context)
        elif strategy == FallbackStrategy.SWITCH_MODEL:
            return self._switch_model(error, context)
        elif strategy == FallbackStrategy.USE_TEMPLATE:
            return self._use_template_response(error, context)
        elif strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
            return self._graceful_degradation(error, context)
        else:
            raise ValueError(f"未知的降级策略: {strategy}")
    
    def _retry_with_backoff(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """指数退避重试"""
        policy = self.retry_policies.get(context.operation_name, RetryPolicy())
        
        if context.retry_count >= policy.max_attempts:
            return FallbackResult(
                success=False,
                response="",
                strategy_used=FallbackStrategy.RETRY_WITH_BACKOFF,
                error_message=f"重试次数已达上限 ({policy.max_attempts})"
            )
        
        # 计算延迟时间
        delay = min(
            policy.base_delay * (policy.exponential_base ** context.retry_count),
            policy.max_delay
        )
        
        if policy.jitter:
            delay *= (0.5 + random.random() * 0.5)  # 添加 50% 的随机抖动
        
        print(f"🔄 重试 {context.operation_name} (第 {context.retry_count + 1} 次，延迟 {delay:.1f}s)")
        time.sleep(delay)
        
        # 这里应该重新执行原始操作，但由于架构限制，我们返回重试指示
        return FallbackResult(
            success=False,  # 需要上层重新执行
            response="",
            strategy_used=FallbackStrategy.RETRY_WITH_BACKOFF,
            additional_data={"should_retry": True, "retry_count": context.retry_count + 1}
        )
    
    def _switch_model(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """切换模型策略"""
        if context.operation_name != "llm_call":
            return FallbackResult(
                success=False,
                response="",
                strategy_used=FallbackStrategy.SWITCH_MODEL,
                error_message="模型切换仅适用于 LLM 调用"
            )
        
        # 返回模型切换指示
        return FallbackResult(
            success=False,  # 需要上层切换模型
            response="",
            strategy_used=FallbackStrategy.SWITCH_MODEL,
            additional_data={"should_switch_model": True}
        )
    
    def _use_template_response(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """使用模板响应"""
        templates = {
            "llm_call": "抱歉，AI 服务暂时不可用。我已记录您的问题，请稍后重试。",
            "tool_call": f"工具 '{context.operation_name}' 暂时不可用，请稍后重试。",
            "command_exec": f"命令执行失败: {context.error_message}",
        }
        
        template = templates.get(
            context.operation_name, 
            f"操作 '{context.operation_name}' 暂时不可用，请稍后重试。"
        )
        
        return FallbackResult(
            success=True,
            response=template,
            strategy_used=FallbackStrategy.USE_TEMPLATE
        )
    
    def _graceful_degradation(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """优雅降级"""
        degraded_response = f"""
⚠️ 系统遇到问题，正在使用降级模式

问题: {context.error_message}
操作: {context.operation_name}
时间: {context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

建议:
• 请检查网络连接
• 稍后重试操作
• 如问题持续，请联系管理员

您的请求已被记录，我们会尽快处理。
"""
        
        return FallbackResult(
            success=True,
            response=degraded_response,
            strategy_used=FallbackStrategy.GRACEFUL_DEGRADATION
        )
    
    def _final_fallback(self, error: Exception, context: ErrorContext) -> FallbackResult:
        """最终降级策略"""
        return FallbackResult(
            success=True,
            response=f"❌ 系统错误: {context.error_message}\n\n请稍后重试或联系管理员。",
            strategy_used=FallbackStrategy.GRACEFUL_DEGRADATION,
            error_message=str(error)
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        with self._lock:
            total_errors = sum(self.error_stats.values())
            total_recoveries = sum(self.recovery_stats.values())
            
            circuit_status = {}
            for name, breaker in self.circuit_breakers.items():
                circuit_status[name] = {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
            
            return {
                "total_errors": total_errors,
                "total_recoveries": total_recoveries,
                "recovery_rate": total_recoveries / max(total_errors, 1),
                "circuit_breakers": circuit_status,
                "error_stats": self.error_stats.copy(),
                "recovery_stats": self.recovery_stats.copy()
            }
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self.error_stats.clear()
            self.recovery_stats.clear()
            self.circuit_breakers.clear()


# 全局韧性管理器实例
resilience_manager = ResilienceManager()


def get_resilience_manager() -> ResilienceManager:
    """获取全局韧性管理器"""
    return resilience_manager


def resilient_operation(operation_name: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR):
    """韧性操作装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            context = ErrorContext(
                error_type=error_type,
                error_message="",
                node_name=func.__name__,
                user_input="",
                operation_name=operation_name
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context.error_message = str(e)
                result = resilience_manager.handle_error(e, context)
                
                if result.success:
                    return {"response": result.response, "error": None}
                else:
                    raise e
        
        return wrapper
    return decorator

