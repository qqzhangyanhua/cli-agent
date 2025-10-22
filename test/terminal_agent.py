#!/usr/bin/env python3
"""
AI智能体终端控制工具 - 模块化重构版本
支持对话功能、记忆功能和MCP工具集成

功能:
- 文件系统访问（读/写/列表/搜索）
- 桌面控制（desktop-commander）
- 终端命令执行
- 智能对话和记忆

运行: python3 terminal_agent.py
"""

from agent_config import AgentState
from agent_memory import memory
from agent_workflow import build_agent
from agent_ui import print_header, handle_special_commands


def main():
    """交互式主循环"""
    
    # 打印欢迎信息
    print_header()
    
    # 构建智能体
    agent = build_agent()
    
    print("🎬 准备就绪！请输入你的指令或问题...\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            special_result = handle_special_commands(user_input)
            if special_result is True:  # 退出
                break
            elif special_result is False:  # 已处理，继续循环
                continue
            
            print()  # 空行
            
            # 构建初始状态
            initial_state: AgentState = {
                "user_input": user_input,
                "intent": "unknown",
                "command": "",
                "commands": [],
                "command_output": "",
                "command_outputs": [],
                "response": "",
                "error": "",
                "needs_file_creation": False,
                "file_path": "",
                "file_content": "",
                "chat_history": [],
                # MCP相关字段
                "mcp_tool": "",
                "mcp_params": {},
                "mcp_result": ""
            }
            
            # 执行工作流
            result = agent.invoke(initial_state)
            
            # 显示响应
            print("─" * 80)
            print(f"🤖 助手: {result['response']}")
            print("─" * 80 + "\n")
            
            # 保存到记忆
            memory.add_interaction(
                user_input, 
                result['response'], 
                result.get('intent', 'unknown')
            )
            
        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，退出程序...\n")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}\n")
            print("请重试或输入 'exit' 退出\n")


if __name__ == "__main__":
    main()
