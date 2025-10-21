# 🚀 AI智能体安装指南

## 📋 系统要求

- **Python**: 3.8+ (推荐 3.11+)
- **操作系统**: macOS, Linux, Windows (WSL)
- **内存**: 最少 512MB 可用内存
- **网络**: 需要访问互联网下载依赖

## 🎯 快速安装

### 1. 一键安装
```bash
cd /path/to/ai-agent/directory
./install.sh
```

### 2. 验证安装
```bash
ai-agent --version
ai-agent --help
```

## 🔧 手动安装

如果自动安装失败，请按以下步骤手动安装：

### 步骤1: 安装Python依赖
```bash
# 方法1: 使用requirements.txt
python3 -m pip install -r requirements.txt --user

# 方法2: 手动安装核心依赖
python3 -m pip install --user langgraph langchain-core langchain-openai httpx requests python-dotenv
```

### 步骤2: 复制程序文件
```bash
# 创建安装目录
mkdir -p ~/.local/bin

# 复制主程序
cp ai-agent ~/.local/bin/
chmod +x ~/.local/bin/ai-agent

# 复制模块文件
cp *.py ~/.local/bin/
cp mcp_config.json ~/.local/bin/
```

### 步骤3: 配置PATH
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## ❗ 常见问题解决

### 问题1: ModuleNotFoundError: No module named 'langgraph'

**原因**: Python依赖未正确安装

**解决方案**:
```bash
# 检查Python版本
python3 --version
which python3

# 重新安装依赖
python3 -m pip install --user langgraph langchain-core langchain-openai

# 如果还是失败，尝试升级pip
python3 -m pip install --upgrade pip
```

### 问题2: ai-agent: command not found

**原因**: PATH配置问题

**解决方案**:
```bash
# 检查安装路径
ls -la ~/.local/bin/ai-agent

# 检查PATH
echo $PATH

# 添加到PATH
export PATH="$HOME/.local/bin:$PATH"

# 永久添加 (选择适合你的shell)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # Bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc   # Zsh

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### 问题3: Python版本不匹配

**原因**: 系统有多个Python版本，pip安装到了错误版本

**解决方案**:
```bash
# 检查Python和pip版本
python3 --version
python3 -m pip --version

# 确保使用正确的pip
python3 -m pip install --user langgraph langchain-core langchain-openai

# 如果有多个Python版本，指定具体版本
python3.11 -m pip install --user langgraph langchain-core langchain-openai
```

### 问题4: 权限错误

**原因**: 没有写入权限

**解决方案**:
```bash
# 使用用户安装模式
python3 -m pip install --user langgraph langchain-core langchain-openai

# 创建用户目录
mkdir -p ~/.local/bin

# 检查目录权限
ls -la ~/.local/
```

### 问题5: 网络连接问题

**原因**: 无法下载依赖包

**解决方案**:
```bash
# 使用国内镜像源
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --user langgraph langchain-core langchain-openai

# 或使用阿里云镜像
python3 -m pip install -i https://mirrors.aliyun.com/pypi/simple/ --user langgraph langchain-core langchain-openai
```

## 🧪 安装验证

### 基本功能测试
```bash
# 1. 版本检查
ai-agent --version

# 2. 帮助信息
ai-agent --help

# 3. 简单命令测试
ai-agent "hello"

# 4. 文件引用功能测试
ai-agent "files"
```

### 交互模式测试
```bash
# 启动交互模式
ai-agent

# 测试基本功能
👤 你: hello
👤 你: files
👤 你: @
👤 你: exit
```

## 🔄 卸载

如果需要卸载AI智能体：

```bash
# 运行卸载脚本
./uninstall.sh

# 或手动删除
rm -f ~/.local/bin/ai-agent
rm -f ~/.local/bin/agent_*.py
rm -f ~/.local/bin/file_reference_parser.py
rm -f ~/.local/bin/interactive_file_selector.py
rm -f ~/.local/bin/mcp_*.py
rm -f ~/.local/bin/git_tools.py
rm -f ~/.local/bin/mcp_config.json
```

## 📞 获取帮助

如果遇到其他问题：

1. **查看日志**: 运行时添加 `-v` 参数查看详细信息
2. **检查配置**: 确认 `mcp_config.json` 和 `agent_config.py` 配置正确
3. **重新安装**: 先卸载再重新安装
4. **环境检查**: 确认Python环境和依赖版本

### 环境信息收集
```bash
# 收集环境信息用于问题诊断
echo "=== 系统信息 ==="
uname -a
echo "=== Python信息 ==="
python3 --version
which python3
python3 -m pip --version
echo "=== PATH信息 ==="
echo $PATH
echo "=== 已安装包 ==="
python3 -m pip list | grep -E "(langgraph|langchain)"
echo "=== 文件权限 ==="
ls -la ~/.local/bin/ai-agent
```

## 🎉 安装成功

安装成功后，您可以：

- ✅ 使用自然语言执行终端命令
- ✅ 通过 `@` 符号交互式选择文件
- ✅ 享受智能对话和记忆功能
- ✅ 使用MCP工具进行文件操作
- ✅ 生成Git commit消息

**开始使用**: `ai-agent` 进入交互模式，输入 `@` 体验文件选择器！
