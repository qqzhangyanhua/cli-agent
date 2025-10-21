# 🤖 AI Agent CLI

一个强大的AI智能终端助手，支持在任何目录下通过自然语言执行命令、操作文件和智能对话。

---

## ✨ 特性

- 🗣️ **自然语言交互** - 用人类语言执行终端命令
- 📁 **文件系统操作** - 读写、搜索、列出文件
- 🖥️ **桌面控制** - 截图、剪贴板操作（集成MCP）
- 🧠 **对话记忆** - 记住上下文，智能理解
- 🎯 **双LLM架构** - 专业模型处理不同任务
- 🚀 **CLI友好** - 支持交互模式和单次执行

---

## 📦 安装

### 方法1: 快速安装（推荐）

```bash
cd /path/to/quantification/example
chmod +x install.sh
./install.sh
```

这会将 `ai-agent` 安装到 `~/.local/bin/`

### 方法2: 自定义路径安装

```bash
./install.sh /usr/local/bin  # 需要sudo权限
```

### 配置PATH

如果 `~/.local/bin` 不在PATH中，添加到 `~/.bashrc` 或 `~/.zshrc`:

```bash
export PATH="${HOME}/.local/bin:${PATH}"
```

然后重新加载配置:

```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

---

## 🚀 使用方法

### 交互模式（推荐）

```bash
ai-agent
```

进入交互模式，可以连续对话：

```
👤 你: 列出当前目录的所有Python文件
🤖 助手: [列出文件...]

👤 你: 读取第一个文件
🤖 助手: [读取文件内容...]

👤 你: 这个文件是做什么的？
🤖 助手: [智能分析...]
```

### 单次命令执行

```bash
# 直接执行命令
ai-agent "列出所有Python文件"

# 执行文件操作
ai-agent "读取README.md文件"

# 执行搜索
ai-agent "搜索包含TODO的文件"
```

### 在特定目录执行

```bash
# 在指定目录执行
ai-agent -w /path/to/project "列出所有文件"

# 先切换目录再执行
cd /path/to/project
ai-agent "列出所有文件"
```

---

## 📖 命令行选项

```bash
ai-agent [选项] [命令]

位置参数:
  command              要执行的命令（可选）

选项:
  -h, --help           显示帮助信息
  -v, --version        显示版本号
  -i, --interactive    强制进入交互模式
  -q, --quiet          安静模式（不显示欢迎信息）
  --no-memory          禁用对话记忆
  -w, --working-dir DIR 设置工作目录
```

---

## 💡 使用示例

### 示例1: 文件操作

```bash
# 读取文件
ai-agent "读取package.json文件"

# 搜索文件
ai-agent "搜索所有包含import的Python文件"

# 列出目录
ai-agent "列出src目录下的所有TypeScript文件"
```

### 示例2: 终端命令

```bash
# 查看系统信息
ai-agent "查看Python版本"

# 查看进程
ai-agent "显示所有Python进程"

# Git操作
ai-agent "显示git状态"
```

### 示例3: 多步骤任务

```bash
# 创建并执行代码
ai-agent "创建一个Python文件hello.py打印Hello World然后执行"

# 数据处理
ai-agent "读取data.csv并统计行数"
```

### 示例4: 智能对话

```bash
# 进入交互模式
ai-agent

👤 你: 列出所有Python文件
🤖 助手: [显示文件列表...]

👤 你: 读取第一个
🤖 助手: [自动识别是哪个文件并读取...]

👤 你: 这个文件是干什么的？
🤖 助手: [基于文件内容智能分析...]
```

---

## 🎯 交互模式特殊命令

在交互模式下，可以使用以下特殊命令：

| 命令 | 功能 |
|------|------|
| `exit` / `quit` | 退出程序 |
| `clear` | 清空对话历史 |
| `history` | 查看对话历史 |
| `commands` | 查看命令执行历史 |
| `models` | 查看当前AI模型配置 |
| `tools` | 查看可用的MCP工具列表 |

---

## 🔧 高级用法

### 在脚本中使用

```bash
#!/bin/bash
# 自动化脚本示例

# 执行分析任务
ai-agent -q "分析当前目录的代码文件" > analysis.txt

# 批量操作
for dir in project1 project2 project3; do
    ai-agent -w "$dir" -q "列出所有Python文件" >> files_list.txt
done
```

### 与管道结合

```bash
# 获取结果并处理
ai-agent "列出所有Python文件" | grep "test"

# 传递输入
echo "分析这个目录" | ai-agent -i
```

### 禁用记忆功能

```bash
# 不保存对话历史（适合一次性任务）
ai-agent --no-memory "执行某个命令"
```

---

## 📁 文件结构

安装后的文件布局：

```
~/.local/bin/
├── ai-agent                  # 主程序
├── agent_config.py           # 配置模块
├── agent_memory.py           # 记忆模块
├── agent_utils.py            # 工具模块
├── agent_llm.py              # LLM初始化
├── agent_nodes.py            # 工作流节点
├── agent_workflow.py         # 工作流构建
├── agent_ui.py               # UI模块
├── mcp_manager.py            # MCP管理器
├── mcp_filesystem.py         # 文件系统工具
└── mcp_config.json           # MCP配置

~/.config/ai-agent/           # 配置目录（可选）
└── ...                       # 未来的配置文件
```

---

## 🛠️ 配置

### 修改LLM配置

编辑 `~/.local/bin/agent_config.py`:

```python
LLM_CONFIG = {
    "model": "your-model",
    "base_url": "your-api-url",
    "api_key": "your-api-key",
    ...
}
```

### 修改工作目录

```bash
# 临时修改（单次使用）
ai-agent -w /path/to/project "命令"

# 永久修改
# 编辑 agent_config.py 中的 WORKING_DIRECTORY
```

---

## 🗑️ 卸载

```bash
cd /path/to/quantification/example
chmod +x uninstall.sh
./uninstall.sh
```

或手动删除：

```bash
rm -f ~/.local/bin/ai-agent
rm -f ~/.local/bin/agent_*.py
rm -f ~/.local/bin/mcp_*.py
rm -f ~/.local/bin/mcp_config.json
```

---

## 🐛 故障排除

### 问题1: 找不到命令

```bash
# 检查PATH
echo $PATH | grep ".local/bin"

# 添加到PATH
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.bashrc
source ~/.bashrc
```

### 问题2: 权限错误

```bash
# 确保有执行权限
chmod +x ~/.local/bin/ai-agent
```

### 问题3: 模块导入错误

```bash
# 确保所有模块文件都已复制
ls ~/.local/bin/agent_*.py

# 重新安装
./install.sh
```

### 问题4: API错误

```bash
# 检查配置
cat ~/.local/bin/agent_config.py

# 确保API密钥正确
# 确保网络连接正常
```

---

## 📊 性能优化

### 加快启动速度

```bash
# 使用安静模式跳过欢迎信息
ai-agent -q "命令"

# 禁用记忆功能（适合一次性任务）
ai-agent --no-memory "命令"
```

### 批量操作

```bash
# 创建批量处理脚本
cat > batch.sh << 'EOF'
#!/bin/bash
for file in *.py; do
    ai-agent -q "分析文件 $file" >> analysis.log
done
EOF

chmod +x batch.sh
./batch.sh
```

---

## 🔐 安全注意事项

1. **API密钥保护**
   - 不要将包含API密钥的配置文件提交到Git
   - 建议使用环境变量存储敏感信息

2. **命令执行安全**
   - 工具会自动拦截危险命令（rm -rf等）
   - 但仍需谨慎使用

3. **文件访问限制**
   - MCP文件系统默认只能访问配置的目录
   - 可在 `mcp_filesystem.py` 中修改

---

## 🆘 获取帮助

```bash
# 查看帮助
ai-agent --help

# 查看版本
ai-agent --version

# 交互模式中查看可用工具
ai-agent
👤 你: tools
```

---

## 🎉 功能演示

### 完整工作流示例

```bash
# 1. 启动交互模式
$ ai-agent

🤖 AI智能终端助手 - 交互式版本 + MCP集成
...

# 2. 分析项目
👤 你: 列出当前目录的所有Python文件

🤖 助手: 找到 8 个文件
  📄 agent_config.py               2.1KB
  📄 agent_memory.py               2.5KB
  ...

# 3. 读取文件
👤 你: 读取agent_config.py

🤖 助手: 
文件大小: 2150 字节
行数: 80

内容:
------------------------------------------------------------
"""
AI智能体配置模块
...

# 4. 智能问答
👤 你: 这个文件主要做什么？

🤖 助手: 这个文件是配置模块，主要负责:
1. 定义LLM配置信息
2. 设置安全参数
3. 定义AgentState数据类型
...

# 5. 执行命令
👤 你: 查看Python版本

🤖 助手: ✅ 命令执行成功

命令: python3 --version

输出:
Python 3.12.2
```

---

## 📝 更新日志

### v1.0.0 (2025-10-21)
- ✅ 首次发布
- ✅ 支持交互模式和单次执行
- ✅ 集成MCP文件系统
- ✅ 支持desktop-commander
- ✅ 双LLM架构
- ✅ 对话记忆功能

---

## 🚀 未来计划

- [ ] 支持配置文件（~/.config/ai-agent/config.json）
- [ ] 插件系统
- [ ] 更多MCP服务器集成
- [ ] 历史命令自动补全
- [ ] 命令别名功能
- [ ] Web界面（可选）

---

## 📄 许可证

MIT License

---

**享受使用 AI Agent CLI！** 🎉

如有问题或建议，欢迎反馈。
