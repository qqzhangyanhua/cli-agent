#!/bin/bash
# AI Agent CLI 卸载脚本

set -e

echo "🗑️  开始卸载 AI Agent CLI..."
echo ""

# 默认安装目录
INSTALL_DIR="${HOME}/.local/bin"

# 检查是否有自定义安装路径
if [ -n "$1" ]; then
    INSTALL_DIR="$1"
fi

echo "📦 卸载目录: ${INSTALL_DIR}"
echo ""

# 删除主程序
if [ -f "${INSTALL_DIR}/ai-agent" ]; then
    echo "🗑️  删除: ${INSTALL_DIR}/ai-agent"
    rm -f "${INSTALL_DIR}/ai-agent"
fi

# 删除模块文件
MODULES=(
    "agent_config.py"
    "agent_memory.py"
    "agent_utils.py"
    "agent_llm.py"
    "agent_nodes.py"
    "agent_workflow.py"
    "agent_ui.py"
    "agent_tool_calling.py"
    "mcp_manager.py"
    "mcp_filesystem.py"
    "mcp_config.json"
    "git_tools.py"
    "git_commit_tools.py"
    "code_review_tools.py"
    "data_converter_tools.py"
    "env_diagnostic_tools.py"
    "file_reference_parser.py"
    "interactive_file_selector.py"
    "todo_manager.py"
    "todo_tools.py"
)

for module in "${MODULES[@]}"; do
    if [ -f "${INSTALL_DIR}/${module}" ]; then
        echo "🗑️  删除: ${INSTALL_DIR}/${module}"
        rm -f "${INSTALL_DIR}/${module}"
    fi
done

# 可选：删除配置目录
CONFIG_DIR="${HOME}/.config/ai-agent"
if [ -d "${CONFIG_DIR}" ]; then
    read -p "是否删除配置目录 ${CONFIG_DIR}? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除配置目录: ${CONFIG_DIR}"
        rm -rf "${CONFIG_DIR}"
    fi
fi

echo ""
echo "✅ 卸载完成！"
