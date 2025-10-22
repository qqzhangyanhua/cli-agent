#!/bin/bash
# AI Agent CLI 安装脚本

set -e

echo "🚀 开始安装 AI Agent CLI..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查Python环境
echo "🐍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "✅ Python版本: ${PYTHON_VERSION}"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到 pip3，请先安装 pip"
    exit 1
fi

# 安装Python依赖
echo ""
echo "📦 安装Python依赖..."
if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "正在安装依赖包..."
    # 使用 python3 -m pip 确保安装到正确的Python版本
    python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" --user --quiet
    if [ $? -eq 0 ]; then
        echo "✅ 依赖安装成功"
    else
        echo "⚠️  依赖安装可能有问题，但继续安装..."
        echo "💡 请手动运行: python3 -m pip install --user langgraph langchain-core langchain-openai"
    fi
else
    echo "⚠️  未找到 requirements.txt，跳过依赖安装"
fi

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
echo "🧪 测试安装..."
if "${INSTALL_DIR}/ai-agent" --version &> /dev/null; then
    echo "✅ 安装测试成功！"
else
    echo "⚠️  安装测试失败，可能需要手动检查依赖"
    echo "请尝试运行: pip3 install --user langgraph langchain-core langchain-openai"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📖 使用方法:"
echo "   ai-agent                      # 进入交互模式"
echo "   ai-agent \"列出所有文件\"      # 执行单条命令"
echo "   ai-agent --help               # 查看帮助"
echo "   ai-agent files                # 查看@文件引用功能"
echo ""
echo "🎯 新功能:"
echo "   • 输入 @ 启动交互式文件选择器"
echo "   • 输入 @文件名 快速搜索文件"
echo "   • 支持自然语言文件操作"
echo ""
echo "🎉 享受使用 AI Agent!"
