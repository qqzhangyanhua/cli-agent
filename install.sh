#!/bin/bash
# AI Agent CLI 安装脚本

set -e

echo "🚀 开始安装 AI Agent CLI..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 默认安装目录
INSTALL_DIR="${HOME}/.local/bin"

# 检查是否有自定义安装路径
if [ -n "$1" ]; then
    INSTALL_DIR="$1"
fi

echo "📦 安装信息:"
echo "   源目录: ${SCRIPT_DIR}"
echo "   安装目录: ${INSTALL_DIR}"
echo ""

# 创建安装目录
if [ ! -d "${INSTALL_DIR}" ]; then
    echo "📁 创建安装目录: ${INSTALL_DIR}"
    mkdir -p "${INSTALL_DIR}"
fi

# 复制主程序
echo "📋 复制程序文件..."
cp "${SCRIPT_DIR}/ai-agent" "${INSTALL_DIR}/ai-agent"
chmod +x "${INSTALL_DIR}/ai-agent"

# 创建配置目录
CONFIG_DIR="${HOME}/.config/ai-agent"
if [ ! -d "${CONFIG_DIR}" ]; then
    echo "📁 创建配置目录: ${CONFIG_DIR}"
    mkdir -p "${CONFIG_DIR}"
fi

# 复制模块文件
echo "📦 复制模块文件..."
MODULES=(
    "agent_config.py"
    "agent_memory.py"
    "agent_utils.py"
    "agent_llm.py"
    "agent_nodes.py"
    "agent_workflow.py"
    "agent_ui.py"
    "mcp_manager.py"
    "mcp_filesystem.py"
    "mcp_config.json"
    "git_tools.py"
)

# 将模块复制到脚本同目录（让ai-agent能找到）
for module in "${MODULES[@]}"; do
    if [ -f "${SCRIPT_DIR}/${module}" ]; then
        cp "${SCRIPT_DIR}/${module}" "${INSTALL_DIR}/${module}"
    else
        echo "⚠️  警告: 找不到 ${module}"
    fi
done

# 检查PATH
echo ""
echo "🔍 检查 PATH 配置..."

if [[ ":$PATH:" == *":${INSTALL_DIR}:"* ]]; then
    echo "✅ ${INSTALL_DIR} 已在 PATH 中"
else
    echo "⚠️  ${INSTALL_DIR} 不在 PATH 中"
    echo ""
    echo "请将以下内容添加到你的 shell 配置文件 (~/.bashrc 或 ~/.zshrc):"
    echo ""
    echo "    export PATH=\"\${HOME}/.local/bin:\${PATH}\""
    echo ""
    echo "然后执行: source ~/.bashrc  (或 source ~/.zshrc)"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📖 使用方法:"
echo "   ai-agent                      # 进入交互模式"
echo "   ai-agent \"列出所有文件\"      # 执行单条命令"
echo "   ai-agent --help               # 查看帮助"
echo ""
echo "🎉 享受使用 AI Agent!"
