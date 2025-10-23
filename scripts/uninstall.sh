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

# 删除模块文件 - 新目录结构
if [ -d "${INSTALL_DIR}/src" ]; then
    echo "🗑️  删除: ${INSTALL_DIR}/src"
    rm -rf "${INSTALL_DIR}/src"
fi

# 删除配置文件
CONFIG_FILES=(
    "mcp_config.json"
    "requirements.txt"
    "INSTALL_MODULES.txt"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "${INSTALL_DIR}/${config_file}" ]; then
        echo "🗑️  删除: ${INSTALL_DIR}/${config_file}"
        rm -f "${INSTALL_DIR}/${config_file}"
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
