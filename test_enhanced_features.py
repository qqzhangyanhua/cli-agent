#!/usr/bin/env python3
"""
增强功能测试脚本
测试错误处理、性能监控和降级策略
"""

import sys
import os
import time
from pathlib import Path

# 添加项目目录到Python路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from src.core.agent_metrics import get_metrics_collector
from src.core.agent_monitoring import get_monitoring_dashboard
from src.core.agent_resilience import get_resilience_manager
from src.core.agent_error_handler import get_llm_fallback_handler, LLMType
from src.core.agent_llm import get_llm_stats, reset_llm_stats
from langchain_core.messages import HumanMessage


def test_metrics_collection():
    """测试性能指标收集"""
    print("🧪 测试性能指标收集...")
    
    metrics = get_metrics_collector()
    
    # 模拟一些操作
    with metrics.measure_operation("test_operation", "test_func") as ctx:
        time.sleep(0.1)  # 模拟耗时操作
        ctx["additional_data"] = {"test": "data"}
    
    # 模拟失败操作
    try:
        with metrics.measure_operation("test_operation", "failing_func"):
            time.sleep(0.05)
            raise Exception("模拟错误")
    except Exception:
        pass
    
    # 检查统计
    stats = metrics.get_session_stats()
    print(f"  ✅ 总操作数: {stats.total_operations}")
    print(f"  ✅ 成功率: {stats.success_rate:.1%}")
    print(f"  ✅ 平均耗时: {stats.average_duration_ms:.1f}ms")
    
    return True


def test_llm_fallback():
    """测试 LLM 降级策略"""
    print("\n🧪 测试 LLM 降级策略...")
    
    handler = get_llm_fallback_handler()
    
    # 测试正常调用
    try:
        messages = [HumanMessage(content="你好")]
        result = handler.call_llm_with_fallback(
            messages=messages,
            llm_type=LLMType.PRIMARY,
            context_type="question"
        )
        
        print(f"  ✅ LLM 调用成功: {result.success}")
        print(f"  ✅ 使用模型: {result.model_used}")
        print(f"  ✅ 响应长度: {len(result.content)} 字符")
        
        if result.token_usage:
            print(f"  ✅ Token 使用: {result.token_usage}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ LLM 测试失败: {e}")
        return False


def test_resilience_manager():
    """测试韧性管理器"""
    print("\n🧪 测试韧性管理器...")
    
    resilience = get_resilience_manager()
    
    # 获取健康状态
    health = resilience.get_health_status()
    print(f"  ✅ 总错误数: {health['total_errors']}")
    print(f"  ✅ 恢复率: {health['recovery_rate']:.1%}")
    print(f"  ✅ 熔断器数量: {len(health['circuit_breakers'])}")
    
    return True


def test_monitoring_dashboard():
    """测试监控仪表板"""
    print("\n🧪 测试监控仪表板...")
    
    dashboard = get_monitoring_dashboard()
    
    # 获取系统健康状态
    health = dashboard.get_system_health()
    print(f"  ✅ 整体状态: {health.overall_status}")
    print(f"  ✅ 性能分数: {health.performance_score:.1f}/100")
    print(f"  ✅ 组件数量: {len(health.components)}")
    
    # 生成快速统计
    quick_stats = dashboard.get_quick_stats()
    print("  ✅ 快速统计:")
    for line in quick_stats.strip().split('\n'):
        print(f"    {line}")
    
    return True


def test_enhanced_llm():
    """测试增强的 LLM 包装器"""
    print("\n🧪 测试增强的 LLM 包装器...")
    
    from src.core.agent_llm import llm, llm_code
    
    try:
        # 测试通用 LLM
        messages = [HumanMessage(content="简单回答：1+1等于多少？")]
        response = llm.invoke(messages, context_type="question")
        
        print(f"  ✅ 通用 LLM 调用成功")
        print(f"  ✅ 响应: {response.content[:50]}...")
        
        # 获取统计信息
        stats = get_llm_stats()
        print(f"  ✅ LLM 统计: {stats['primary_llm']['call_count']} 次调用")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 增强 LLM 测试失败: {e}")
        return False


def test_mcp_monitoring():
    """测试 MCP 工具监控"""
    print("\n🧪 测试 MCP 工具监控...")
    
    try:
        from src.mcp.mcp_manager import mcp_manager
        
        # 测试工具调用（使用内置工具）
        result = mcp_manager.call_tool("read_file", file_path="README.md")
        
        print(f"  ✅ MCP 工具调用: {'成功' if result.get('success') else '失败'}")
        
        # 检查指标收集
        metrics = get_metrics_collector()
        tool_stats = metrics.get_operation_stats("tool_call")
        print(f"  ✅ 工具调用统计: {tool_stats['count']} 次")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP 监控测试失败: {e}")
        return False


def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始增强功能综合测试")
    print("=" * 60)
    
    tests = [
        ("性能指标收集", test_metrics_collection),
        ("LLM 降级策略", test_llm_fallback),
        ("韧性管理器", test_resilience_manager),
        ("监控仪表板", test_monitoring_dashboard),
        ("增强 LLM", test_enhanced_llm),
        ("MCP 工具监控", test_mcp_monitoring),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{len(results)} 项测试通过")
    
    # 显示最终统计
    print("\n📈 最终性能统计:")
    dashboard = get_monitoring_dashboard()
    print(dashboard.get_quick_stats())
    
    return passed == len(results)


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)



