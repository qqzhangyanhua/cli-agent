#!/usr/bin/env python3
"""
自动生成安装脚本中的模块列表
通过分析 agent_nodes.py 和 agent_workflow.py 的导入语句来自动发现所有需要的模块
"""

import re
from pathlib import Path
from typing import Set, List


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """
    从 Python 文件中提取本地模块的导入
    
    Args:
        file_path: Python 文件路径
    
    Returns:
        导入的本地模块名称集合
    """
    imports = set()
    
    if not file_path.exists():
        return imports
    
    content = file_path.read_text(encoding='utf-8')
    
    # 匹配 from xxx import ...
    pattern1 = r'^from\s+(\w+)\s+import'
    # 匹配 import xxx
    pattern2 = r'^import\s+(\w+)'
    
    for line in content.split('\n'):
        line = line.strip()
        
        # from xxx import ...
        match = re.match(pattern1, line)
        if match:
            module_name = match.group(1)
            # 过滤掉标准库和第三方库
            if not module_name.startswith('_') and module_name not in [
                'json', 'os', 'sys', 're', 'datetime', 'pathlib', 'typing',
                'subprocess', 'langchain', 'langgraph', 'langchain_core',
                'langchain_openai', 'openai'
            ]:
                imports.add(module_name)
        
        # import xxx
        match = re.match(pattern2, line)
        if match:
            module_name = match.group(1)
            if not module_name.startswith('_') and module_name not in [
                'json', 'os', 'sys', 're', 'datetime', 'pathlib', 'typing',
                'subprocess', 'langchain', 'langgraph', 'langchain_core',
                'langchain_openapi', 'openai'
            ]:
                imports.add(module_name)
    
    return imports


def find_all_required_modules(source_dir: Path) -> List[str]:
    """
    查找所有需要的模块文件
    
    Args:
        source_dir: 源代码目录
    
    Returns:
        模块文件列表
    """
    # 核心入口文件
    core_files = [
        'ai-agent',
        'agent_config.py',
        'agent_workflow.py',
        'agent_nodes.py',
        'agent_tool_calling.py',
    ]
    
    all_modules = set()
    processed = set()
    to_process = set(core_files)
    
    # 递归查找所有依赖
    while to_process:
        current_file = to_process.pop()
        if current_file in processed:
            continue
        
        processed.add(current_file)
        file_path = source_dir / current_file
        
        if not file_path.exists():
            continue
        
        # 提取导入
        imports = extract_imports_from_file(file_path)
        
        for module_name in imports:
            module_file = f"{module_name}.py"
            if (source_dir / module_file).exists():
                all_modules.add(module_file)
                if module_file not in processed:
                    to_process.add(module_file)
    
    # 添加必需的配置文件
    all_modules.add('mcp_config.json')
    
    # 排序
    return sorted(all_modules)


def generate_bash_array(modules: List[str]) -> str:
    """
    生成 Bash 数组格式的模块列表
    
    Args:
        modules: 模块列表
    
    Returns:
        Bash 数组字符串
    """
    lines = ['MODULES=(']
    for module in modules:
        lines.append(f'    "{module}"')
    lines.append(')')
    return '\n'.join(lines)


if __name__ == "__main__":
    source_dir = Path(__file__).parent
    
    print("🔍 自动发现项目模块...")
    print()
    
    modules = find_all_required_modules(source_dir)
    
    print(f"📊 发现 {len(modules)} 个模块文件:\n")
    for i, module in enumerate(modules, 1):
        exists = "✅" if (source_dir / module).exists() else "❌"
        print(f"  {i:2d}. {exists} {module}")
    
    print("\n" + "=" * 60)
    print("📋 Bash 数组格式（用于 install.sh）:\n")
    print(generate_bash_array(modules))
    print("\n" + "=" * 60)
    
    # 写入文件
    output_file = source_dir / "INSTALL_MODULES.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# AI Agent 安装模块列表\n")
        f.write("# 自动生成于: " + __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write(generate_bash_array(modules))
        f.write("\n")
    
    print(f"\n💾 模块列表已保存到: {output_file}")
    print("\n💡 提示: 将上面的 MODULES=(...) 复制到 install.sh 和 uninstall.sh 中")

