# 🤖 AI Agent CLI - 智能终端助手

> 一个强大的 AI 终端助手，让你用自然语言控制命令行！支持文件操作、代码执行、MCP 集成和智能文件引用。

## ✨ 核心特性

- 🗣️ **自然语言执行命令** - 用人话说，让 AI 执行终端命令
- 📁 **@ 智能文件引用** - 交互式文件选择器，快速引用和操作文件
- 🧠 **对话记忆** - 记住上下文，支持连续对话
- 🔌 **MCP 集成** - 文件系统和桌面控制功能
- 🎯 **双 LLM 配置** - 通用模型处理对话，代码模型生成命令
- 🚀 **创建并执行代码** - 一句话生成并运行代码
- 📝 **Git 智能工具** - 自动生成 commit 消息、代码审查（Code Review）

---

## 📦 快速安装

### 步骤1: 克隆并安装

```bash
cd /Users/zhangyanhua/Desktop/AI/tushare/quantification/example
./install.sh
```

### 步骤2: 配置 PATH（如果需要）

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.zshrc
source ~/.zshrc
```

### 步骤3: 验证安装

```bash
ai-agent --version
```

看到版本号 `1.0.0` 就成功了！✅

---

## 🎯 使用方式

### 🌟 方式1: 交互模式（推荐）

直接启动进入对话模式：

```bash
ai-agent
```

然后就可以自然对话了：

```
👤 你: 列出所有Python文件
👤 你: 读取README.md
👤 你: 这是做什么的？
👤 你: 创建一个hello.py打印Hello World然后执行
```

### ⚡ 方式2: 单次命令模式

适合脚本调用或快速执行：

```bash
ai-agent "列出所有Python文件"
ai-agent "读取README.md文件"
ai-agent "搜索包含TODO的文件"
ai-agent "显示git状态"
```

### 📂 方式3: 指定工作目录

在特定目录执行任务：

```bash
ai-agent -w /path/to/project "列出所有文件"
ai-agent --working-dir ~/projects/myapp "查看Python版本"
```

### 🔕 方式4: 安静模式

只输出结果，不显示格式：

```bash
ai-agent -q "列出所有Python文件"
ai-agent --quiet "查看当前目录"
```

---

## 💡 使用示例

### 📁 文件操作示例

```bash
# 读取文件
ai-agent "读取package.json"
ai-agent "显示README.md的内容"

# 列出文件
ai-agent "列出所有Python文件"
ai-agent "显示当前目录的所有.js文件"

# 搜索文件
ai-agent "搜索包含LLM_CONFIG的文件"
ai-agent "查找所有包含TODO的文件"

# 写入文件
ai-agent "创建test.txt文件并写入Hello World"
```

### 🖥️ 终端命令示例

```bash
# 查看系统信息
ai-agent "查看Python版本"
ai-agent "显示当前目录的磁盘使用情况"

# 进程管理
ai-agent "显示所有Python进程"
ai-agent "查看端口8080的占用情况"

# Git操作
ai-agent "显示git状态"
ai-agent "查看最近5次提交记录"

# Git智能功能
ai-agent "生成commit消息"  # 智能分析代码变更并生成规范的commit消息
ai-agent "对当前代码进行code review"  # 智能代码审查，按严重性分级报告问题
```

### 🚀 创建和执行代码

```bash
# 创建并运行
ai-agent "创建hello.py打印Hello World然后执行"
ai-agent "写一个Python脚本计算1到100的和并运行"

# 批量操作
ai-agent "创建10个测试文件test1.txt到test10.txt"
```

### 📝 智能问答

```bash
# 分析代码
ai-agent "这个项目是做什么的？"
ai-agent "agent_config.py里有什么配置项？"

# 技术咨询
ai-agent "如何在Python中读取JSON文件？"
ai-agent "解释一下LangGraph的工作原理"
```

---

## 🎨 交互模式特殊命令

进入交互模式后，除了正常对话，还支持以下特殊命令：

| 命令 | 说明 |
|------|------|
| `tools` / `工具` | 查看所有可用的 MCP 工具列表 |
| `models` / `模型` | 查看双 LLM 模型配置详情 |
| `files` / `文件` / `@` | 查看 @ 文件引用功能说明 |
| `history` / `历史` | 查看完整对话历史记录 |
| `commands` / `命令` | 查看已执行的命令历史 |
| `clear` / `清空` | 清空对话历史和上下文 |
| `exit` / `quit` / `退出` | 退出程序 |

---

## 🔥 @ 文件引用功能

这是 `ai-agent` 的杀手级功能！让你快速引用文件到对话上下文中。

### 基本用法

```bash
# 方式1: 直接输入 @ 启动交互式文件选择器
👤 你: @
🎯 启动文件选择器...
[显示文件列表，数字选择]

# 方式2: 输入 @ 加部分文件名快速搜索
👤 你: @read
🔍 搜索文件: 'read'...
[显示匹配的文件列表]

# 方式3: 直接引用文件路径
👤 你: 读取 @README.md
👤 你: @config.py 的配置项有哪些？
👤 你: 比较 @old.txt 和 @new.txt 的差异
```

### 支持的语法

- `@filename.ext` - 智能匹配文件名
- `@./path/file.ext` - 相对路径
- `@/absolute/path` - 绝对路径
- `@*.py` - 通配符匹配
- `@folder/` - 目录引用

### 交互式选择器功能

- 🔢 数字快速选择
- 🔍 实时搜索和过滤
- 📄 文件大小和图标显示
- 📑 支持分页浏览
- ⌨️ 快捷键操作（`n`下一页，`p`上一页，`h`显示隐藏文件）

### 使用示例

```bash
# 启动交互模式
ai-agent

# 在对话中使用 @
👤 你: @
🎯 启动文件选择器...
[选择 agent_config.py]
✅ 已选择文件: @agent_config.py
👤 你: 这个文件里有什么配置？

# 快速搜索
👤 你: @agent
🔍 搜索文件: 'agent'...
1. 🐍 agent_config.py
2. 🐍 agent_nodes.py
3. 🐍 agent_workflow.py
👤 选择文件 (输入数字): 1
```

---

## 🔧 命令行选项

```bash
ai-agent [选项] [命令]

选项:
  -h, --help                显示帮助信息
  -v, --version             显示版本号
  -i, --interactive         强制进入交互模式
  -q, --quiet               安静模式，不显示欢迎信息
  -w, --working-dir DIR     设置工作目录（默认：当前目录）
  --no-memory               禁用对话记忆功能

示例:
  ai-agent                            # 交互模式
  ai-agent "列出所有Python文件"       # 单次命令
  ai-agent -w ~/project "git status"  # 指定目录
  ai-agent -q "pwd"                   # 安静模式
  ai-agent --no-memory                # 禁用记忆
```

---

## ⚙️ 配置说明

### 修改 AI 模型

编辑 `~/.local/bin/agent_config.py`：

```python
# 通用模型配置（用于对话和理解）
LLM_CONFIG = {
    "model": "qwen-plus",
    "api_key": "your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.7,
}

# 代码模型配置（用于命令生成和代码编写）
LLM_CONFIG2 = {
    "model": "qwen-coder-plus",
    "api_key": "your-api-key", 
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.1,
}
```

### MCP 工具配置

编辑 `~/.local/bin/mcp_config.json`：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    }
  }
}
```

---

## 🗑️ 卸载

```bash
cd /Users/zhangyanhua/Desktop/AI/tushare/quantification/example
./uninstall.sh
```

会自动清理：
- `~/.local/bin/ai-agent` 及相关文件
- 安装的 Python 模块
- MCP 配置文件

---

## 🏗️ 技术架构

### 核心技术栈

- **LangGraph** - 工作流编排引擎
- **LangChain** - LLM 应用框架
- **MCP (Model Context Protocol)** - 工具集成协议
- **双 LLM 架构** - 专业分工，各司其职

### 工作流程

```
用户输入 → 意图分析 → 工作流路由
                    ↓
         ┌──────────┼──────────┐
         ↓          ↓          ↓
    命令执行    文件操作    智能问答
         ↓          ↓          ↓
         └──────────┼──────────┘
                    ↓
              结果生成 → 记忆存储
```

### 模块说明

| 模块 | 文件 | 功能 |
|------|------|------|
| 入口程序 | `ai-agent` | CLI 入口，参数解析 |
| 配置管理 | `agent_config.py` | 双 LLM 配置 |
| 工作流 | `agent_workflow.py` | LangGraph 工作流定义 |
| 节点实现 | `agent_nodes.py` | 各种处理节点 |
| 记忆系统 | `agent_memory.py` | 对话历史管理 |
| MCP 集成 | `mcp_manager.py` | MCP 工具管理 |
| 文件引用 | `file_reference_parser.py` | @ 语法解析 |
| 文件选择器 | `interactive_file_selector.py` | 交互式文件选择 |
| UI 界面 | `agent_ui.py` | 用户界面和提示 |

---

## 📚 更多文档

- **[CLI_README.md](CLI_README.md)** - 完整 CLI 使用文档
- **[AT_FEATURE_DEMO.md](AT_FEATURE_DEMO.md)** - @ 文件引用功能演示
- **[INTERACTIVE_FILE_SELECTOR_GUIDE.md](INTERACTIVE_FILE_SELECTOR_GUIDE.md)** - 文件选择器详细指南
- **[MCP_INTEGRATION_COMPLETE.md](MCP_INTEGRATION_COMPLETE.md)** - MCP 集成完整说明
- **[DUAL_LLM_CONFIG.md](DUAL_LLM_CONFIG.md)** - 双 LLM 配置指南
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - 代码重构说明

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 克隆仓库
git clone <your-repo-url>
cd example

# 安装依赖
pip install -r requirements.txt

# 运行测试
python terminal_agent.py
```

### 代码规范

- 使用 Python 3.8+
- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写单元测试

---

## 📄 许可证

MIT License

---

## 🎉 开始使用

```bash
ai-agent
```

**就这么简单！** 开始享受 AI 助手带来的便利吧！🚀

### 快速上手

1. ✅ 安装完成后，直接输入 `ai-agent` 启动
2. 💬 用自然语言描述你想做什么
3. 📁 使用 `@` 快速引用文件
4. 🔍 输入 `tools` 查看所有可用功能
5. 💡 输入 `files` 了解文件引用技巧

---

<div align="center">

**Made with ❤️ using LangGraph & LangChain**

如果觉得有用，请给个 ⭐️ Star！

</div>
