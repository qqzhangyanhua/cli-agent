# 🚀 AI Agent CLI - 快速开始

## 📦 5分钟安装指南

### 步骤1: 安装

```bash
cd /Users/zhangyanhua/Desktop/AI/tushare/quantification/example
./install.sh
```

### 步骤2: 配置PATH（如果需要）

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.zshrc
source ~/.zshrc
```

### 步骤3: 测试

```bash
ai-agent --version
```

看到版本号就成功了！✅

---

## 🎯 3种使用方式

### 方式1: 交互模式（推荐新手）

```bash
ai-agent
```

然后就可以对话了：

```
👤 你: 列出所有Python文件
👤 你: 读取README.md
👤 你: 这是做什么的？
```

### 方式2: 单次命令（推荐脚本）

```bash
ai-agent "列出所有Python文件"
ai-agent "读取README.md文件"
ai-agent "搜索包含TODO的文件"
```

### 方式3: 指定目录执行

```bash
ai-agent -w /path/to/project "列出所有文件"
```

---

## 💡 常用命令示例

### 文件操作
```bash
# 读取文件
ai-agent "读取package.json"

# 列出文件
ai-agent "列出所有Python文件"

# 搜索文件
ai-agent "搜索包含import的文件"
```

### 终端命令
```bash
# 查看版本
ai-agent "查看Python版本"

# 查看进程
ai-agent "显示所有Python进程"

# Git操作
ai-agent "显示git状态"
```

### 创建和执行
```bash
# 创建并执行代码
ai-agent "创建hello.py打印Hello World然后执行"
```

---

## 🎨 交互模式特殊命令

进入交互模式后可以使用：

- `tools` - 查看所有可用工具
- `models` - 查看AI模型配置
- `history` - 查看对话历史
- `commands` - 查看命令历史
- `clear` - 清空历史
- `exit` - 退出

---

## 🔧 自定义配置

### 修改AI模型

编辑 `~/.local/bin/agent_config.py`：

```python
LLM_CONFIG = {
    "model": "your-preferred-model",
    "api_key": "your-api-key",
    ...
}
```

### 修改默认工作目录

同样编辑 `agent_config.py`：

```python
WORKING_DIRECTORY = "/your/default/path"
```

---

## 🗑️ 卸载

```bash
cd /Users/zhangyanhua/Desktop/AI/tushare/quantification/example
./uninstall.sh
```

---

## 📚 更多文档

- **CLI_README.md** - 完整CLI使用文档
- **REFACTORING_SUMMARY.md** - 代码重构说明
- **MCP_INTEGRATION_DONE.md** - MCP集成说明

---

## 🎉 开始使用

```bash
ai-agent
```

**就这么简单！** 开始享受AI助手吧！🚀
