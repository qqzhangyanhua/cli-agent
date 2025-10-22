#!/usr/bin/env python3
"""
安装验证脚本 - 检查所有必需的模块是否存在
"""

import sys
from pathlib import Path

# 所有必需的模块文件
REQUIRED_MODULES = [
    "agent_config.py",
    "agent_memory.py",
    "agent_utils.py",
    "agent_llm.py",
    "agent_nodes.py",
    "agent_workflow.py",
    "agent_ui.py",
    "agent_tool_calling.py",
    "mcp_manager.py",
    "mcp_filesystem.py",
    "mcp_config.json",
    "git_tools.py",
    "git_commit_tools.py",
    "code_review_tools.py",
    "data_converter_tools.py",
    "env_diagnostic_tools.py",
    "file_reference_parser.py",
    "interactive_file_selector.py",
    "todo_manager.py",
    "todo_tools.py",
]

def verify_modules(base_dir: Path) -> bool:
    """
    验证所有必需的模块是否存在
    
    Args:
        base_dir: 基础目录路径
    
    Returns:
        验证是否通过
    """
    print("🔍 验证安装模块...")
    print(f"📁 检查目录: {base_dir}")
    print()
    
    missing_modules = []
    found_modules = []
    
    for module in REQUIRED_MODULES:
        module_path = base_dir / module
        if module_path.exists():
            found_modules.append(module)
            print(f"  ✅ {module}")
        else:
            missing_modules.append(module)
            print(f"  ❌ {module} (缺失)")
    
    print()
    print(f"📊 统计:")
    print(f"  • 找到: {len(found_modules)}/{len(REQUIRED_MODULES)}")
    print(f"  • 缺失: {len(missing_modules)}/{len(REQUIRED_MODULES)}")
    
    if missing_modules:
        print()
        print("⚠️  缺失的模块:")
        for module in missing_modules:
            print(f"    - {module}")
        print()
        print("💡 建议: 运行 ./install.sh 重新安装")
        return False
    else:
        print()
        print("✅ 所有模块都已正确安装！")
        return True


if __name__ == "__main__":
    # 获取当前脚本所在目录（源代码目录）
    source_dir = Path(__file__).parent
    
    # 安装目录
    install_dir = Path.home() / ".local" / "bin"
    
    print("=" * 60)
    print("AI Agent 安装验证")
    print("=" * 60)
    print()
    
    # 验证源代码目录
    print("📋 验证源代码目录...")
    print()
    source_ok = verify_modules(source_dir)
    
    print()
    print("─" * 60)
    print()
    
    # 验证安装目录
    print("📋 验证安装目录...")
    print()
    install_ok = verify_modules(install_dir)
    
    print()
    print("=" * 60)
    
    if source_ok and install_ok:
        print("🎉 验证通过！所有模块都已正确安装。")
        sys.exit(0)
    else:
        print("❌ 验证失败！请检查缺失的模块。")
        sys.exit(1)

