"""
系统监控和仪表板模块
提供实时性能监控、健康检查和统计报告
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from src.core.agent_metrics import get_metrics_collector, SessionStats
from src.core.agent_resilience import get_resilience_manager
from src.core.agent_error_handler import get_llm_fallback_handler


@dataclass
class SystemHealth:
    """系统健康状态"""
    overall_status: str  # "healthy", "degraded", "critical"
    timestamp: datetime
    components: Dict[str, Dict[str, Any]]
    performance_score: float  # 0-100
    recommendations: List[str]


class MonitoringDashboard:
    """监控仪表板"""
    
    def __init__(self):
        self.metrics = get_metrics_collector()
        self.resilience = get_resilience_manager()
        self.llm_handler = get_llm_fallback_handler()
        
        # 监控配置
        self.health_check_interval = 60  # 秒
        self.performance_threshold = {
            "avg_response_time_ms": 5000,  # 5秒
            "success_rate": 0.95,  # 95%
            "error_rate": 0.05,  # 5%
            "token_usage_per_hour": 50000  # 每小时50k tokens
        }
        
        # 监控状态
        self._monitoring_active = False
        self._monitor_thread = None
        self._last_health_check = None
    
    def start_monitoring(self):
        """启动监控"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="SystemMonitor"
        )
        self._monitor_thread.start()
        print("📊 系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self._monitoring_active:
            return
            
        self._monitoring_active = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            try:
                # 减少超时时间，因为监控循环现在响应更快
                self._monitor_thread.join(timeout=2)
                if self._monitor_thread.is_alive():
                    print("📊 系统监控线程未能及时停止，但程序将继续退出")
                else:
                    print("📊 系统监控已停止")
            except KeyboardInterrupt:
                # 如果在等待线程结束时被中断，直接返回
                print("📊 系统监控强制停止")
                return
        else:
            print("📊 系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self._monitoring_active:
            try:
                # 执行健康检查
                health = self.get_system_health()
                
                # 检查是否需要告警
                if health.overall_status in ["degraded", "critical"]:
                    self._send_alert(health)
                
                # 更新最后检查时间
                self._last_health_check = datetime.now()
                
                # 等待下次检查，使用短间隔检查停止标志
                for _ in range(self.health_check_interval):
                    if not self._monitoring_active:
                        return
                    time.sleep(1)
                
            except Exception as e:
                if self._monitoring_active:  # 只在活跃时打印错误
                    print(f"⚠️ 监控循环异常: {e}")
                # 异常后短暂等待，同样检查停止标志
                for _ in range(10):
                    if not self._monitoring_active:
                        return
                    time.sleep(1)
    
    def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        components = {}
        recommendations = []
        
        # 1. 性能指标检查
        session_stats = self.metrics.get_session_stats()
        perf_component = self._check_performance_health(session_stats)
        components["performance"] = perf_component
        
        if perf_component["status"] != "healthy":
            recommendations.extend(perf_component.get("recommendations", []))
        
        # 2. 错误率检查
        resilience_status = self.resilience.get_health_status()
        error_component = self._check_error_health(resilience_status)
        components["error_handling"] = error_component
        
        if error_component["status"] != "healthy":
            recommendations.extend(error_component.get("recommendations", []))
        
        # 3. LLM 健康检查
        llm_component = self._check_llm_health()
        components["llm_services"] = llm_component
        
        if llm_component["status"] != "healthy":
            recommendations.extend(llm_component.get("recommendations", []))
        
        # 4. 资源使用检查
        resource_component = self._check_resource_usage(session_stats)
        components["resources"] = resource_component
        
        if resource_component["status"] != "healthy":
            recommendations.extend(resource_component.get("recommendations", []))
        
        # 计算整体状态和性能分数
        overall_status, performance_score = self._calculate_overall_status(components)
        
        return SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now(),
            components=components,
            performance_score=performance_score,
            recommendations=recommendations
        )
    
    def _check_performance_health(self, stats: SessionStats) -> Dict[str, Any]:
        """检查性能健康状态"""
        status = "healthy"
        issues = []
        recommendations = []
        
        # 检查平均响应时间
        if stats.average_duration_ms > self.performance_threshold["avg_response_time_ms"]:
            status = "degraded"
            issues.append(f"平均响应时间过长: {stats.average_duration_ms:.1f}ms")
            recommendations.append("考虑优化 LLM 调用或增加缓存")
        
        # 检查成功率
        if stats.success_rate < self.performance_threshold["success_rate"]:
            status = "critical" if stats.success_rate < 0.8 else "degraded"
            issues.append(f"成功率过低: {stats.success_rate:.1%}")
            recommendations.append("检查网络连接和服务可用性")
        
        return {
            "status": status,
            "metrics": {
                "avg_response_time_ms": stats.average_duration_ms,
                "success_rate": stats.success_rate,
                "total_operations": stats.total_operations,
                "session_duration_minutes": stats.session_duration_minutes
            },
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_error_health(self, resilience_status: Dict[str, Any]) -> Dict[str, Any]:
        """检查错误处理健康状态"""
        status = "healthy"
        issues = []
        recommendations = []
        
        total_errors = resilience_status["total_errors"]
        recovery_rate = resilience_status["recovery_rate"]
        
        # 检查错误率
        if total_errors > 10:  # 超过10个错误
            status = "degraded"
            issues.append(f"错误数量较多: {total_errors}")
            recommendations.append("检查系统日志，识别错误模式")
        
        # 检查恢复率
        if recovery_rate < 0.8 and total_errors > 0:
            status = "critical" if recovery_rate < 0.5 else "degraded"
            issues.append(f"错误恢复率低: {recovery_rate:.1%}")
            recommendations.append("检查降级策略配置")
        
        # 检查熔断器状态
        circuit_breakers = resilience_status["circuit_breakers"]
        open_breakers = [name for name, state in circuit_breakers.items() if state["state"] == "OPEN"]
        
        if open_breakers:
            status = "critical"
            issues.append(f"熔断器打开: {', '.join(open_breakers)}")
            recommendations.append("检查相关服务状态，等待自动恢复")
        
        return {
            "status": status,
            "metrics": {
                "total_errors": total_errors,
                "recovery_rate": recovery_rate,
                "open_circuit_breakers": len(open_breakers)
            },
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_llm_health(self) -> Dict[str, Any]:
        """检查 LLM 服务健康状态"""
        status = "healthy"
        issues = []
        recommendations = []
        
        # 获取 LLM 状态（这里简化处理）
        model_status = self.llm_handler.get_model_health_status()
        
        # 检查模型可用性（实际实现中需要进行真实的健康检查）
        # 这里只是示例逻辑
        
        return {
            "status": status,
            "metrics": {
                "primary_model": model_status["primary_model"]["name"],
                "secondary_model": model_status["secondary_model"]["name"],
                "models_available": 2
            },
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_resource_usage(self, stats: SessionStats) -> Dict[str, Any]:
        """检查资源使用状态"""
        status = "healthy"
        issues = []
        recommendations = []
        
        # 检查 Token 使用
        total_tokens = stats.total_tokens["total_tokens"]
        session_hours = max(stats.session_duration_minutes / 60, 0.1)  # 至少0.1小时
        tokens_per_hour = total_tokens / session_hours
        
        if tokens_per_hour > self.performance_threshold["token_usage_per_hour"]:
            status = "degraded"
            issues.append(f"Token 使用率过高: {tokens_per_hour:.0f}/小时")
            recommendations.append("优化提示词长度，减少不必要的 LLM 调用")
        
        return {
            "status": status,
            "metrics": {
                "total_tokens": total_tokens,
                "tokens_per_hour": tokens_per_hour,
                "session_duration_hours": session_hours
            },
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _calculate_overall_status(self, components: Dict[str, Dict]) -> tuple[str, float]:
        """计算整体状态和性能分数"""
        status_weights = {
            "healthy": 100,
            "degraded": 60,
            "critical": 20
        }
        
        component_weights = {
            "performance": 0.3,
            "error_handling": 0.3,
            "llm_services": 0.25,
            "resources": 0.15
        }
        
        total_score = 0
        critical_count = 0
        degraded_count = 0
        
        for comp_name, comp_data in components.items():
            comp_status = comp_data["status"]
            weight = component_weights.get(comp_name, 0.1)
            score = status_weights[comp_status]
            
            total_score += score * weight
            
            if comp_status == "critical":
                critical_count += 1
            elif comp_status == "degraded":
                degraded_count += 1
        
        # 确定整体状态
        if critical_count > 0:
            overall_status = "critical"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return overall_status, total_score
    
    def _send_alert(self, health: SystemHealth):
        """发送告警"""
        alert_message = f"""
🚨 系统健康告警

状态: {health.overall_status.upper()}
时间: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
性能分数: {health.performance_score:.1f}/100

问题组件:
"""
        
        for comp_name, comp_data in health.components.items():
            if comp_data["status"] != "healthy":
                alert_message += f"• {comp_name}: {comp_data['status']}\n"
                for issue in comp_data.get("issues", []):
                    alert_message += f"  - {issue}\n"
        
        if health.recommendations:
            alert_message += "\n建议措施:\n"
            for rec in health.recommendations:
                alert_message += f"• {rec}\n"
        
        print(alert_message)
        
        # 这里可以扩展为发送邮件、Webhook 等
    
    def generate_performance_report(self, detailed: bool = False) -> str:
        """生成性能报告"""
        health = self.get_system_health()
        stats = self.metrics.get_session_stats()
        
        report = f"""
📊 系统性能报告
{'=' * 60}

🎯 整体状态: {health.overall_status.upper()}
📈 性能分数: {health.performance_score:.1f}/100
⏰ 报告时间: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

📋 会话统计:
   持续时间: {stats.session_duration_minutes:.1f} 分钟
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
"""
        
        if detailed:
            report += "\n🔍 组件详情:\n"
            for comp_name, comp_data in health.components.items():
                report += f"\n• {comp_name.upper()}: {comp_data['status']}\n"
                
                if comp_data.get("metrics"):
                    for key, value in comp_data["metrics"].items():
                        if isinstance(value, float):
                            report += f"  {key}: {value:.2f}\n"
                        else:
                            report += f"  {key}: {value}\n"
                
                if comp_data.get("issues"):
                    report += "  问题:\n"
                    for issue in comp_data["issues"]:
                        report += f"    - {issue}\n"
        
        if health.recommendations:
            report += "\n💡 优化建议:\n"
            for rec in health.recommendations:
                report += f"• {rec}\n"
        
        return report
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """导出指标数据"""
        if not filepath:
            filepath = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "system_health": asdict(self.get_system_health()),
            "session_stats": asdict(self.metrics.get_session_stats()),
            "recent_metrics": [asdict(m) for m in self.metrics.get_recent_metrics(100)],
            "resilience_status": self.resilience.get_health_status()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath
    
    def get_quick_stats(self) -> str:
        """获取快速统计信息"""
        stats = self.metrics.get_session_stats()
        health = self.get_system_health()
        
        status_emoji = {
            "healthy": "🟢",
            "degraded": "🟡", 
            "critical": "🔴"
        }
        
        return f"""
{status_emoji.get(health.overall_status, '⚪')} 系统状态: {health.overall_status.upper()}
⏱️ 会话时长: {stats.session_duration_minutes:.1f}分钟
🎯 成功率: {stats.success_rate:.1%}
🪙 Token: {stats.total_tokens['total_tokens']:,}
🔧 操作数: {stats.total_operations}
"""


# 全局监控仪表板实例
monitoring_dashboard = MonitoringDashboard()


def get_monitoring_dashboard() -> MonitoringDashboard:
    """获取全局监控仪表板"""
    return monitoring_dashboard
