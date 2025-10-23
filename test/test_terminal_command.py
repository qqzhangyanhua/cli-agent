#!/usr/bin/env python3
"""
测试终端命令功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_config import AgentState
from agent_tool_calling import simple_tool_calling_node

def test_terminal_command():
    """测试终端命令识别和执行"""
    
    test_cases = [
        "列出当前目录下的json文件",
        "查看Python版本", 
        "显示当前路径",
        "ls *.py",
        "创建一个test文件夹"
    ]
    
    print("🧪 测试终端命令功能")
    print("─" * 80)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_input}")
        print("─" * 40)
        
        # 创建测试状态
        state = AgentState(
            user_input=test_input,
            intent="",
            response="",
            command="",
            commands=[],
            file_contents={},
            referenced_files=[],
            memory_context="",
            error=""
        )
        
        try:
            # 调用工具选择节点
            result = simple_tool_calling_node(state)
            
            print(f"✅ 识别意图: {result.get('intent', 'unknown')}")
            if result.get('response'):
                print(f"📄 响应: {result['response']}")
            
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
        
        print()

if __name__ == "__main__":
    test_terminal_command()
