# 📁 @ 文件引用功能演示

## 🎯 功能概述

AI智能体现在支持强大的 **@ 文件引用功能**，让您可以在自然语言中直接引用和操作文件，就像在现代编辑器中一样！

## 🚀 基本用法

### 1. 直接文件引用
```bash
# 启动 AI 智能体
./ai-agent

# 使用 @ 引用文件
👤 你: 读取 @README.md
👤 你: @agent_config.py 中的配置有哪些？
👤 你: 分析 @mcp_config.json 的结构
```

### 2. 文件操作
```bash
👤 你: 编辑 @agent_config.py 修改API密钥
👤 你: 在 @README.md 中添加新的功能说明
👤 你: 备份 @重要文件.txt 到backup目录
```

### 3. 文件比较和分析
```bash
👤 你: 比较 @old_config.py 和 @new_config.py 的差异
👤 你: @*.py 文件中哪些使用了LLM_CONFIG？
👤 你: 分析 @项目目录/ 的结构
```

## 📝 支持的语法

| 语法格式 | 说明 | 示例 |
|---------|------|------|
| `@filename.ext` | 智能匹配文件名 | `@config.py` |
| `@./path/file.ext` | 相对路径 | `@./src/main.py` |
| `@/absolute/path` | 绝对路径 | `@/home/user/file.txt` |
| `@*.ext` | 通配符匹配 | `@*.py` |
| `@folder/` | 目录引用 | `@src/` |

## 🔍 智能匹配特性

### 自动文件搜索
- ✅ 当前目录优先匹配
- ✅ 递归搜索子目录（最大3层）
- ✅ 部分文件名匹配
- ✅ 相似度评分和排序

### 错误处理和建议
```bash
👤 你: 读取 @不存在的文件.txt
🤖 助手: 
[文件引用] ⚠️  文件不存在: 不存在的文件.txt
[文件引用] 💡 建议的文件: config.py, README.md, agent_ui.py
```

## 💡 实际使用示例

### 示例 1: 配置文件分析
```bash
👤 你: @agent_config.py 中配置了哪些LLM模型？

🤖 助手: 
[文件引用] 检查输入中的 @ 引用...
[文件引用] 发现 1 个文件引用
📁 文件引用解析结果:
  1. ✅ 📄 /path/to/agent_config.py (100.0%)
[文件引用] ✅ 已读取: /path/to/agent_config.py (2847 字符)

根据 agent_config.py 文件，配置了以下LLM模型：

1. **通用LLM配置 (LLM_CONFIG)**:
   - 模型: kimi-k2-0905-preview
   - 用途: 意图分析、问答等

2. **代码生成LLM配置 (LLM_CONFIG2)**:
   - 模型: claude-3-5-sonnet  
   - 用途: 生成命令和代码
```

### 示例 2: 多文件比较
```bash
👤 你: 比较 @agent_config.py 和 @mcp_config.json 的配置方式

🤖 助手:
[文件引用] 发现 2 个文件引用
[文件引用] ✅ 已读取: agent_config.py (2847 字符)
[文件引用] ✅ 已读取: mcp_config.json (456 字符)

这两个配置文件采用了不同的配置方式：

**agent_config.py (Python配置)**:
- 使用Python字典定义配置
- 包含LLM模型、安全设置、工作目录等
- 支持类型注解和文档字符串

**mcp_config.json (JSON配置)**:
- 使用JSON格式存储MCP服务器配置
- 结构化的服务器列表和参数
- 易于程序解析和修改
```

### 示例 3: 代码编辑
```bash
👤 你: 在 @agent_config.py 中添加新的安全配置项

🤖 助手:
[文件引用] ✅ 已读取: agent_config.py

我将为您在 agent_config.py 中添加新的安全配置项...

[执行文件编辑操作]
✅ 已在 DANGEROUS_COMMANDS 列表中添加新的危险命令
✅ 添加了 ALLOWED_EXTENSIONS 配置项
✅ 增加了 MAX_FILE_SIZE 限制配置
```

## 🛠️ 技术实现

### 核心组件
1. **FileReferenceParser**: @ 语法解析器
2. **file_reference_processor**: 工作流预处理节点  
3. **智能匹配算法**: 文件搜索和相似度计算
4. **MCP集成**: 文件系统操作

### 工作流程
```
用户输入 → @ 语法解析 → 文件匹配 → 内容读取 → 意图分析 → 执行操作
```

## 📊 性能特性

- ⚡ **快速匹配**: 智能缓存和索引
- 🔒 **安全控制**: 路径验证和权限检查  
- 📝 **内存优化**: 大文件分块处理
- 🎯 **精确匹配**: 多级匹配策略

## 🎉 开始使用

1. **启动智能体**:
   ```bash
   ./ai-agent
   ```

2. **查看帮助**:
   ```bash
   👤 你: files
   # 显示 @ 功能完整说明
   ```

3. **试试这些命令**:
   ```bash
   👤 你: 读取 @README.md
   👤 你: @agent_config.py 的配置项有哪些？
   👤 你: 编辑 @test.txt 添加一些内容
   ```

---

🎊 **恭喜！您现在可以像专业开发者一样，在AI对话中直接引用和操作文件了！**
