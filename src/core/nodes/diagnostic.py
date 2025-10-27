"""
环境诊断节点
检测和诊断开发环境配置
"""

import json
from src.core.agent_config import AgentState
from src.tools.env_diagnostic_tools import env_diagnostic_tools


def environment_diagnostic_processor(state: AgentState) -> dict:
    """
    环境诊断处理节点
    检测和诊断开发环境配置
    """
    print(f"\n[环境诊断] 开始诊断...")

    try:
        # 执行完整诊断
        result = env_diagnostic_tools.full_diagnostic()

        if result["success"]:
            report = result["report"]

            # 格式化报告
            formatted_report = env_diagnostic_tools.format_report(report)

            print(f"[环境诊断] ✅ 诊断完成")

            return {
                "response": formatted_report,
                "diagnostic_result": json.dumps(report, ensure_ascii=False)
            }
        else:
            error_msg = result.get("error", "未知错误")
            print(f"[环境诊断] ❌ 诊断失败: {error_msg}")
            return {
                "response": f"❌ 环境诊断失败\n\n错误: {error_msg}",
                "error": error_msg
            }

    except Exception as e:
        print(f"[环境诊断] ❌ 异常: {e}")
        return {
            "response": f"❌ 环境诊断出错: {str(e)}",
            "error": str(e)
        }
