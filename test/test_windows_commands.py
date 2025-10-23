#!/usr/bin/env python3
"""
测试Windows平台命令生成
验证在Windows系统上生成正确的命令
"""

import platform
from langchain_core.messages import HumanMessage
from agent_llm import llm_code
from agent_config import LLM_CONFIG2


def test_command_generation(user_input: str) -> str:
    """测试命令生成"""
    
    os_type = platform.system()
    
    # 根据操作系统设置示例
    if os_type == "Windows":
        examples = """示例（Windows）:
- "列出当前目录的所有文件" -> dir 或 Get-ChildItem
- "查看Python版本" -> python --version
- "显示当前路径" -> cd
- "查看文件内容" -> type filename.txt 或 Get-Content filename.txt
- "创建目录" -> mkdir dirname
- "删除文件" -> del filename
- "复制文件" -> copy source dest
- "移动文件" -> move source dest"""
    else:
        examples = """示例（Unix/Linux/macOS）:
- "列出当前目录的所有文件" -> ls -la
- "查看Python版本" -> python3 --version
- "显示当前路径" -> pwd
- "查看文件内容" -> cat filename.txt
- "创建目录" -> mkdir dirname
- "删除文件" -> rm filename
- "复制文件" -> cp source dest
- "移动文件" -> mv source dest"""

    prompt = f"""将用户的自然语言请求转换为终端命令。

操作系统: {os_type}

当前请求: {user_input}

{examples}

**重要**: 
- 必须生成适合 {os_type} 系统的命令
- 只返回命令本身，不要解释
- 不要添加注释或说明

命令:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    command = result.content.strip()
    
    return command


def main():
    """主测试函数"""
    print("=" * 80)
    print("Windows 命令生成测试")
    print("=" * 80)
    print()
    
    os_type = platform.system()
    print(f"📟 当前操作系统: {os_type}")
    print(f"🤖 使用模型: {LLM_CONFIG2['model']}")
    print()
    print("─" * 80)
    
    # 测试用例
    test_cases = [
        "当前目录下有哪些文件",
        "列出所有文件",
        "查看Python版本",
        "显示当前路径",
        "创建一个名为test的目录",
        "查看README.md的内容",
    ]
    
    for idx, test_input in enumerate(test_cases, 1):
        print(f"\n测试 {idx}: {test_input}")
        print("─" * 40)
        
        try:
            command = test_command_generation(test_input)
            print(f"✅ 生成命令: {command}")
            
            # 验证Windows命令
            if os_type == "Windows":
                # 检查是否包含常见的Unix命令（应该避免）
                unix_commands = ["ls", "pwd", "cat", "rm ", "cp ", "mv "]
                has_unix = any(cmd in command.lower() for cmd in unix_commands)
                
                if has_unix:
                    print(f"⚠️  警告: 在Windows系统上生成了Unix命令！")
                else:
                    print(f"✅ 命令适合Windows系统")
                    
        except Exception as e:
            print(f"❌ 生成失败: {e}")
    
    print()
    print("─" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

