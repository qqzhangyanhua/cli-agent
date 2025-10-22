# Code Review 功能完整实现指南

## 📋 功能概述

基于 git diff 的智能代码审查功能，自动分析代码变更，发现潜在问题，并按严重性分级（🔴 严重、🟡 中级、🟢 普通）输出详细的审查报告。

## 🎯 设计目标

1. **自动化审查**：无需手动指定文件，自动分析所有 git 变更
2. **智能分析**：使用 LLM 深度理解代码逻辑，发现潜在问题
3. **分级报告**：按严重性分级，帮助开发者优先处理关键问题
4. **可操作建议**：提供具体、可执行的改进建议

## 🏗️ 架构设计

### 核心模块

```
code_review_tools.py          # 核心实现模块
├── analyze_code_changes()    # 分析 git diff
├── perform_code_review_func() # 执行代码审查（LLM驱动）
└── code_review_tool          # LangChain Tool 封装

agent_tool_calling.py         # 工具调用集成
├── simple_tool_calling_node() # 添加 code_review 识别
└── 工具路由逻辑              # 调用 code_review_tool

agent_workflow.py             # 工作流路由
└── route_by_intent()         # 添加 code_review 意图路由
```

### 工作流程

```
用户输入
    ↓
"对当前待提交的代码进行code-review"
    ↓
agent_tool_calling.py
    ↓
LLM 识别意图 → "code_review"
    ↓
调用 code_review_tool.func()
    ↓
code_review_tools.py
    ↓
1. 检查 git 仓库
2. 获取 git diff (staged + unstaged)
3. 合并 diff 内容
4. 构建详细的审查 prompt
5. 调用 LLM (llm_code) 分析
6. 格式化审查报告
    ↓
返回分级报告
    ↓
工作流结束 (END)
```

## 📁 实现细节

### 1. code_review_tools.py

#### analyze_code_changes()

**功能**：分析 git 变更，合并 staged 和 unstaged 的 diff

**返回结构**：
```python
{
    "success": bool,
    "diff_content": str,      # 合并后的 diff 内容
    "files_changed": list,    # 变更的文件列表
    "summary": str,           # 变更摘要
    "error": str              # 错误信息（如果有）
}
```

**特性**：
- 同时获取 staged 和 unstaged 的变更
- 清晰标记每部分的来源
- 自动去重文件列表
- 生成简洁的摘要

#### perform_code_review_func()

**功能**：执行完整的代码审查流程

**Prompt 设计要点**：

1. **审查维度**（5个方面）：
   - 安全性 (Security)
   - 性能 (Performance)  
   - 代码质量 (Code Quality)
   - 最佳实践 (Best Practices)
   - 代码风格 (Code Style)

2. **问题分级**：
   - 🔴 严重 (Critical)：安全漏洞、关键bug、破坏性变更
   - 🟡 中级 (Medium)：潜在bug、性能问题、最佳实践违反
   - 🟢 普通 (Minor)：代码风格、命名建议、优化建议

3. **输出格式**：
   ```
   📊 代码审查概览
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   • 审查文件: X 个
   • 发现问题: Y 个（🔴严重 A个，🟡中级 B个，🟢普通 C个）
   • 审查结论: [通过/需要修改/存在严重问题]
   
   🔴 严重问题 (A个)
   [具体问题列表...]
   
   🟡 中级问题 (B个)
   [具体问题列表...]
   
   🟢 普通问题 (C个)
   [具体问题列表...]
   
   ✅ 表现良好的方面
   [列出优点...]
   
   💡 总体建议
   [改进建议...]
   ```

#### code_review_tool

**LangChain Tool 封装**：
- 名称：`code_review`
- 描述：详细说明适用场景和功能
- 函数：`perform_code_review_func`
- 参数：无需参数（自动获取 git diff）

### 2. agent_tool_calling.py 集成

#### 修改点

1. **导入模块**：
   ```python
   from code_review_tools import code_review_tool
   ```

2. **更新工具列表**（在 prompt 中）：
   ```python
   4. code_review - 代码审查
      参数: 无（自动分析git diff）
      适用场景: "代码审查"、"code review"、"检查代码"、"review代码"
   ```

3. **添加工具调用逻辑**：
   ```python
   elif tool_name == "code_review":
       result_text = code_review_tool.func("")
       return {
           "intent": "code_review",
           "response": result_text
       }
   ```

### 3. agent_workflow.py 路由

#### 修改点

在 `route_by_intent()` 函数中添加 `code_review` 意图：

```python
if intent in ["add_todo", "query_todo", "git_commit", "code_review"]:
    # 工具调用节点已完成处理，直接结束
    return "end"
```

**设计理由**：code_review 工具已经生成完整的报告，无需进入其他节点处理。

## 💡 使用方法

### 方式1：CLI 交互式使用（推荐）

```bash
$ ./ai-agent

🤖 你好！我是AI终端助手。

👤 你: 对当前待提交的代码进行code-review

[工具选择] 分析用户意图...
[工具选择] 选择工具: code_review
[Code Review] 开始代码审查...
[Code Review] ✅ 分析完成
[Code Review] 共 3 个文件有变更
[Code Review] 使用模型: deepseek/deepseek-chat
[Code Review] 正在生成审查报告...
[Code Review] ✅ 审查完成

📝 代码审查报告已生成

📊 代码审查概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 审查文件: 3 个
• 发现问题: 5 个（🔴严重 0个，🟡中级 2个，🟢普通 3个）
• 审查结论: 代码质量良好，建议修复中级问题

...（详细报告）
```

### 方式2：命令行直接调用

```bash
$ ./ai-agent "对当前代码进行code review"
```

### 方式3：Python API 调用

```python
from code_review_tools import perform_code_review_func

# 直接调用
result = perform_code_review_func()
print(result)
```

### 方式4：LangChain Tool 调用

```python
from code_review_tools import code_review_tool

# 作为 LangChain Tool 使用
result = code_review_tool.func("")
print(result)
```

## 🔍 用户输入示例

支持的自然语言输入（会自动识别）：

- ✅ "对当前待提交的代码进行code-review"
- ✅ "代码审查"
- ✅ "code review"
- ✅ "检查我的代码"
- ✅ "帮我review一下代码"
- ✅ "代码有什么问题吗"
- ✅ "review当前的修改"
- ✅ "分析一下代码质量"

## 📊 输出示例

```
📝 代码审查报告已生成

📊 代码审查概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 审查文件: 3 个
• 发现问题: 5 个（🔴严重 0个，🟡中级 2个，🟢普通 3个）
• 审查结论: 代码质量良好，建议修复中级问题

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 严重问题 (0个)

无严重问题。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 中级问题 (2个)

1. [code_review_tools.py:analyze_code_changes] 错误处理不完善
   
   问题描述：
   函数没有处理 git_tools.get_git_diff() 可能抛出的异常
   
   建议：
   添加 try-except 块捕获可能的异常：
   ```python
   try:
       unstaged_diff = git_tools.get_git_diff(staged=False)
       staged_diff = git_tools.get_git_diff(staged=True)
   except Exception as e:
       return {"success": False, "error": f"获取 diff 失败: {str(e)}"}
   ```

2. [code_review_tools.py:perform_code_review_func] 性能优化
   
   问题描述：
   当 diff 内容非常大时，截断到 10000 字符可能丢失重要信息
   
   建议：
   考虑按文件分批审查，或提供配置项让用户选择审查深度

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 普通问题 (3个)

1. [code_review_tools.py:16] 类型注解
   
   问题描述：
   analyze_code_changes() 的返回类型用 Dict 比较泛化
   
   建议：
   使用 TypedDict 定义更精确的返回类型

2. [code_review_tools.py:97] 代码注释
   
   问题描述：
   复杂的 prompt 构建逻辑缺少内联注释
   
   建议：
   添加注释说明 prompt 设计思路

3. [agent_tool_calling.py:171] 代码重复
   
   问题描述：
   注释中"优先选择"的逻辑重复
   
   建议：
   统一注释格式，避免重复表述

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 表现良好的方面

• 模块化设计清晰，职责分离良好
• 使用了 emoji 增强用户体验
• 错误处理较为完善，有友好的错误提示
• 文档字符串完整，符合规范
• 遵循了项目的代码风格

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 总体建议

1. 优先修复中级问题中的错误处理问题
2. 考虑为大型 diff 添加分批审查功能
3. 添加单元测试覆盖核心功能
4. 考虑添加配置项，允许用户自定义审查严格度
```

## 🎨 设计特点

### 1. 智能意图识别

- LLM 自动识别 code review 相关的各种表述
- 支持中英文混合输入
- 关键词触发：code review、代码审查、检查代码、review 等

### 2. 全面的审查维度

基于业界最佳实践，从 5 个维度审查代码：
- 安全性：防止安全漏洞
- 性能：优化执行效率
- 代码质量：提高可维护性
- 最佳实践：遵循行业规范
- 代码风格：保持一致性

### 3. 科学的分级系统

**🔴 严重问题**：
- 必须立即修复
- 影响系统安全和稳定性
- 可能导致数据丢失或崩溃

**🟡 中级问题**：
- 建议修复
- 影响代码质量和性能
- 违反最佳实践

**🟢 普通问题**：
- 可选修复
- 主要是风格和优化建议
- 不影响功能

### 4. 可操作的建议

每个问题都包含：
- 📍 具体位置（文件名、函数名、行号）
- 📝 详细描述（为什么是问题）
- 💡 改进建议（如何修复）
- 💻 代码示例（可能的话）

### 5. 双 LLM 架构

- 使用 `llm_code`（代码模型）进行代码分析
- 专门针对代码理解和分析优化
- 配置在 `agent_config.py` 的 `LLM_CONFIG2`

## 🔧 配置说明

### LLM 配置

代码审查使用 `LLM_CONFIG2`（代码模型），在 `agent_config.py` 中配置：

```python
LLM_CONFIG2 = {
    "model": "deepseek/deepseek-chat",  # 或其他代码专用模型
    "temperature": 0.1,                 # 低温度保证稳定性
    "max_tokens": 4096                  # 足够的输出长度
}
```

### Diff 长度限制

在 `code_review_tools.py` 中可调整：

```python
max_diff_length = 10000  # 增加这个值以分析更大的 diff
```

### Prompt 自定义

如需调整审查标准，修改 `perform_code_review_func()` 中的 prompt。

## 🧪 测试

### 运行测试

```bash
# 方式1：直接运行测试文件
$ python test/test_code_review.py

# 方式2：使用 pytest
$ pytest test/test_code_review.py -v

# 方式3：集成测试
$ ./test/test_integration.sh
```

### 测试覆盖

- ✅ 基础功能测试（`test_code_review_func`）
- ✅ Tool 封装测试（`test_code_review_tool`）
- ✅ 意图识别测试（通过 CLI 测试）
- ✅ 工作流集成测试（通过 integration test）

## 📚 参考资料

### 相关模块
- `git_tools.py` - Git 操作工具
- `git_commit_tools.py` - Git Commit 消息生成（类似架构）
- `agent_tool_calling.py` - 工具调用系统
- `agent_workflow.py` - LangGraph 工作流

### 技术栈
- LangChain - Tool 封装和 LLM 调用
- LangGraph - 工作流管理
- Git - 代码变更分析

## 🚀 未来改进方向

1. **分批审查**：支持对大型 diff 分文件审查
2. **历史对比**：对比历史审查结果，追踪代码质量趋势
3. **自定义规则**：允许用户添加项目特定的审查规则
4. **增量审查**：只审查变更的部分，提高效率
5. **团队规范**：集成团队的 code review checklist
6. **自动修复**：对于简单问题，提供自动修复选项
7. **报告导出**：支持导出 Markdown/PDF 格式的报告

## 📝 开发日志

- **2025-10-22**：完整实现 Code Review 功能
  - 创建 `code_review_tools.py` 模块
  - 集成到工具调用系统
  - 更新工作流路由
  - 添加测试和文档

## 🤝 贡献

欢迎贡献！如果你有改进建议或发现问题，请：

1. 提交 Issue 描述问题或建议
2. Fork 项目并创建功能分支
3. 提交 Pull Request

---

**作者**: AI Agent CLI Team  
**最后更新**: 2025-10-22  
**版本**: 1.0.0

