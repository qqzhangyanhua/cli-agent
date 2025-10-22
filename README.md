# 🤖 DNM智能体终端控制工具 - 智能终端助手

> 一个强大的 AI 终端助手，让你用自然语言控制命令行！支持文件操作、代码执行、MCP 集成和智能文件引用。

## ✨ 核心特性

- 🗣️ **自然语言执行命令** - 用人话说，让 AI 执行终端命令
- 📁 **@ 智能文件引用** - IDE 风格自动补全，实时搜索过滤（全新升级！）
- 🧠 **对话记忆** - 记住上下文，支持连续对话
- 📝 **Git 完整工作流** - 一键完成 pull → commit → push，自动识别分支
  - 智能生成 commit 消息（基于代码分析）
  - 自动分支识别（dev/main/feature 等）
  - 支持单独 pull/push 操作
  - 完整的 5 步骤工作流或 3 步骤提交
- 🔍 **代码审查** - AI 驱动的代码质量分析
- 📊 **数据转换工具** - JSON/CSV/YAML/XML 格式互转、验证
- 🔍 **环境诊断** - 自动检测开发环境配置和依赖问题
- 📋 **待办事项管理** - 智能识别并管理日程安排和任务提醒
- 🔌 **MCP 集成** - 文件系统和桌面控制功能
- 🎯 **双 LLM 配置** - 通用模型处理对话，代码模型生成命令
- 🚀 **创建并执行代码** - 一句话生成并运行代码

---

## 📦 快速安装

### 跨平台安装（推荐）

使用 Python 安装脚本，支持 Windows、macOS 和 Linux：

```bash
# 克隆项目
git clone <repository-url>
cd cli-agent

# 使用 Python 安装脚本
python install.py

# 如果需要自定义安装目录
python install.py --dir /your/custom/path
```

### Windows 安装

#### 方法1: PowerShell 脚本（推荐）

```powershell
# 在 PowerShell 中运行（需要管理员权限或允许执行策略）
powershell -ExecutionPolicy Bypass -File install.ps1
```

#### 方法2: Python 脚本

```powershell
python install.py
```

安装后，`dnm` 命令会被添加到系统 PATH。重新打开终端即可使用。

### macOS / Linux 安装

#### 方法1: Bash 脚本

```bash
cd cli-agent
./install.sh
```

#### 方法2: Python 脚本

```bash
python3 install.py
```

### 配置 PATH（如果需要）

**macOS / Linux:**
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:**
安装脚本会自动提示配置 PATH，或手动添加：
1. 右键 "此电脑" -> "属性" -> "高级系统设置"
2. 点击 "环境变量"
3. 在 "用户变量" 中编辑 "Path"
4. 添加安装目录（通常是 `%LOCALAPPDATA%\Programs\dnm`）

### 验证安装

```bash
dnm --version
```

看到版本号 `1.0.0` 就成功了！✅

### Windows 编码兼容性

本项目已经针对 Windows 平台的编码问题进行了全面修复。所有 Git 命令和终端操作都能正确处理 UTF-8 编码的输出。

如果遇到编码相关错误（如 `UnicodeDecodeError`），请参考 [docs/WINDOWS_ENCODING_FIX.md](docs/WINDOWS_ENCODING_FIX.md) 获取详细说明和解决方案。

---

## 🎯 使用方式

### 🌟 方式1: 交互模式（推荐）

直接启动进入对话模式：

```bash
dnm
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
dnm "列出所有Python文件"
dnm "读取README.md文件"
dnm "搜索包含TODO的文件"
dnm "显示git状态"
```

### 📂 方式3: 指定工作目录

在特定目录执行任务：

```bash
dnm -w /path/to/project "列出所有文件"
dnm --working-dir ~/projects/myapp "查看Python版本"
```

### 🔕 方式4: 安静模式

只输出结果，不显示格式：

```bash
dnm -q "列出所有Python文件"
dnm --quiet "查看当前目录"
```

---

## 💡 使用示例

### 📁 文件操作示例

```bash
# 读取文件
dnm "读取package.json"
dnm "显示README.md的内容"

# 列出文件
dnm "列出所有Python文件"
dnm "显示当前目录的所有.js文件"

# 搜索文件
dnm "搜索包含LLM_CONFIG的文件"
dnm "查找所有包含TODO的文件"

# 写入文件
dnm "创建test.txt文件并写入Hello World"
```

### 🖥️ 终端命令示例

```bash
# 查看系统信息
dnm "查看Python版本"
dnm "显示当前目录的磁盘使用情况"

# 进程管理
dnm "显示所有Python进程"
dnm "查看端口8080的占用情况"

# Git基础操作
dnm "显示git状态"
dnm "查看最近5次提交记录"

# Git智能功能
dnm "生成commit消息"           # 仅生成commit消息，不提交
dnm "提交代码"                 # 3步骤：add -> 生成消息 -> commit
dnm "同步并提交"               # 5步骤：pull -> add -> 生成消息 -> commit -> push
dnm "拉取代码"                 # 仅执行 git pull
dnm "推送代码"                 # 仅执行 git push（自动识别分支 dev/main 等）
dnm "对当前代码进行code review"  # AI代码审查，按严重性分级报告问题

# 数据转换功能
dnm "@data.json 转换为CSV"  # JSON转CSV格式
dnm "@config.yaml 转换为JSON"  # YAML转JSON格式
dnm "@data.json 验证格式"  # 验证JSON格式是否正确
dnm "@config.json 美化格式"  # 格式化JSON使其更易读

# 环境诊断功能
dnm "检查开发环境"  # 诊断Python环境、依赖、工具等
dnm "诊断环境配置"  # 检测环境问题并提供修复建议

# 待办事项管理
dnm "今天18点给陈龙打电话"  # 添加待办事项
dnm "明天上午10点开会"  # 添加日程安排
dnm "今天有什么要做的"  # 查询今日待办
dnm "搜索陈龙相关的待办"  # 搜索特定关键词的待办
```

### 🚀 创建和执行代码

```bash
# 创建并运行
dnm "创建hello.py打印Hello World然后执行"
dnm "写一个Python脚本计算1到100的和并运行"

# 批量操作
dnm "创建10个测试文件test1.txt到test10.txt"
```

### 📝 智能问答

```bash
# 分析代码
dnm "这个项目是做什么的？"
dnm "agent_config.py里有什么配置项？"

# 技术咨询
dnm "如何在Python中读取JSON文件？"
dnm "解释一下LangGraph的工作原理"
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
| `todos` / `待办` | 查看今日待办事项 |
| `help` / `帮助` | 显示功能帮助信息 |
| `exit` / `quit` / `退出` | 退出程序 |

---

## 🔥 @ 文件引用功能 ⚡ 全新升级！

这是 `ai-agent` 的杀手级功能！现已升级为 **IDE 风格的自动补全体验**，类似 Codex/Claude Code！

### ✨ 新特性（v1.0.0）

- 🎯 **实时自动补全** - 输入 `@` 后立即显示文件列表，无需额外操作
- 🔍 **智能模糊搜索** - 支持缩写和部分匹配（如 `@cfg` → `agent_config.py`）
- ⌨️ **流畅键盘操作** - 上下箭头选择，Tab 补全，Enter 确认
- 📝 **历史记录** - 自动保存输入历史，支持快速回溯
- 🎨 **丰富图标** - 根据文件类型显示不同图标和文件大小
- 📂 **递归扫描** - 自动索引子目录文件，支持路径补全

### 基本用法

```bash
# 方式1: IDE 风格自动补全（推荐）✨
👤 你: @
# 立即弹出文件列表：
#   🐍 agent_config.py (3.2K)
#   🐍 agent_workflow.py (8.5K)
#   📝 README.md (12.3K)
#   ...

# 继续输入过滤
👤 你: @read
# 自动过滤显示匹配文件
#   📝 README.md (12.3K)
#   📝 README_INTERACTIVE.md (5.1K)
# 使用 ↑↓ 选择，Enter 确认

# 方式2: 模糊搜索
👤 你: @cfg      # 匹配 agent_config.py
👤 你: @wkf      # 匹配 agent_workflow.py
👤 你: @ui       # 匹配 agent_ui.py

# 方式3: 直接引用文件路径
👤 你: 读取 @README.md
👤 你: @config.py 的配置项有哪些？
👤 你: 比较 @old.txt 和 @new.txt 的差异
```

### 支持的语法

- `@filename.ext` - 智能匹配文件名（支持模糊搜索）
- `@./path/file.ext` - 相对路径
- `@/absolute/path` - 绝对路径
- `@docs/README.md` - 子目录文件
- 多文件引用：`比较 @file1 和 @file2`

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `↑` `↓` | 选择文件 |
| `Tab` | 补全当前项 |
| `Enter` | 确认选择 |
| `Ctrl+C` | 取消输入 |

### 使用示例

```bash
# 启动交互模式
dnm

# 🌟 新体验：输入 @ 后继续输入
👤 你: @read
[实时显示匹配文件]
📝 README.md (12.3K)
📝 README_INTERACTIVE.md (5.1K)
[使用 ↑↓ 选择，Enter 确认]

👤 你: @README.md 总结这个项目
🤖 助手: 这是一个 AI 智能体终端控制工具...

# 模糊搜索示例
👤 你: @cfg 有哪些配置项？
# 自动匹配 agent_config.py

👤 你: 比较 @agent_config.py 和 @agent_llm.py
# 多文件引用
```

### 安装增强功能

新的 IDE 风格补全需要 `prompt-toolkit`：

```bash
# 自动安装（推荐）
python install_prompt_toolkit.py

# 或手动安装
pip install prompt-toolkit>=3.0.0
```

如果未安装，系统会自动降级到传统的文件选择器模式。

### 📚 详细文档

- **[UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)** - 升级指南和功能对比
- **[docs/SMART_FILE_REFERENCE.md](docs/SMART_FILE_REFERENCE.md)** - 完整功能文档
- **[demo_smart_file_input.py](demo_smart_file_input.py)** - 交互式演示

---

## 🔧 命令行选项

```bash
dnm [选项] [命令]

选项:
  -h, --help                显示帮助信息
  -v, --version             显示版本号
  -i, --interactive         强制进入交互模式
  -q, --quiet               安静模式，不显示欢迎信息
  -w, --working-dir DIR     设置工作目录（默认：当前目录）
  --no-memory               禁用对话记忆功能

示例:
  dnm                            # 交互模式
  dnm "列出所有Python文件"       # 单次命令
  dnm -w ~/project "git status"  # 指定目录
  dnm -q "pwd"                   # 安静模式
  dnm --no-memory                # 禁用记忆
```

---

## ⚙️ 配置说明

### 修改 AI 模型

编辑配置文件 `agent_config.py`：

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

编辑配置文件 `mcp_config.json`：

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
- `~/.local/bin/dnm` 及相关文件
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
| 入口程序 | `dnm` | CLI 入口，参数解析 |
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

### 🎯 功能指南
- **[docs/GIT_AUTO_COMMIT_WORKFLOW.md](docs/GIT_AUTO_COMMIT_WORKFLOW.md)** - Git 完整工作流详细实现（pull → commit → push）
- **[docs/GIT_AUTO_COMMIT_QUICK_START.md](docs/GIT_AUTO_COMMIT_QUICK_START.md)** - Git 自动提交快速开始
- **[docs/new_features_guide.md](docs/new_features_guide.md)** - 数据转换和环境诊断功能详细指南
- **[docs/AT_FEATURE_DEMO.md](docs/AT_FEATURE_DEMO.md)** - @ 文件引用功能演示
- **[docs/TODO_FEATURE_GUIDE.md](docs/TODO_FEATURE_GUIDE.md)** - 待办事项管理功能指南
- **[docs/CODE_REVIEW_FEATURE.md](docs/CODE_REVIEW_FEATURE.md)** - 代码审查功能说明

### 🔧 技术文档
- **[docs/CLI_README.md](docs/CLI_README.md)** - 完整 CLI 使用文档
- **[docs/INTERACTIVE_FILE_SELECTOR_GUIDE.md](docs/INTERACTIVE_FILE_SELECTOR_GUIDE.md)** - 文件选择器详细指南
- **[docs/MCP_INTEGRATION_COMPLETE.md](docs/MCP_INTEGRATION_COMPLETE.md)** - MCP 集成完整说明
- **[docs/DUAL_LLM_CONFIG.md](docs/DUAL_LLM_CONFIG.md)** - 双 LLM 配置指南
- **[docs/REFACTORING_SUMMARY.md](docs/REFACTORING_SUMMARY.md)** - 代码重构说明

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
dnm
```

**就这么简单！** 开始享受 AI 助手带来的便利吧！🚀

### 快速上手

1. ✅ 安装完成后，直接输入 `dnm` 启动
2. 💬 用自然语言描述你想做什么
3. 📁 使用 `@` 快速引用文件
4. 🔍 输入 `tools` 查看所有可用功能
5. 💡 输入 `help` 查看功能帮助
6. 📋 输入 `todos` 查看待办事项
7. 🎯 尝试 Git 工作流：`同步并提交`（自动 pull → commit → push）
8. 🎯 尝试数据转换：`@data.json 转换为CSV`
9. 🔍 尝试环境诊断：`检查开发环境`

---

<div align="center">

**Made with ❤️ using LangGraph & LangChain**

如果觉得有用，请给个 ⭐️ Star！

</div>
