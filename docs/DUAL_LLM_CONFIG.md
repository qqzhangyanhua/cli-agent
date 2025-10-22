# 🔧 双LLM配置说明

## 📋 概述

系统现在支持**双LLM配置**，针对不同任务使用不同的大语言模型，提升性能和准确性：

- **LLM_CONFIG** - 通用模型：用于意图分析、对话、问答
- **LLM_CONFIG2** - 代码专家模型：用于生成命令、编写代码

## 🎯 使用场景

### LLM_CONFIG（通用模型）
**使用场景：**
- ✅ 意图分析（判断用户想做什么）
- ✅ 对话问答（回答用户问题）
- ✅ 上下文理解（理解对话历史）

**推荐模型：**
- GPT-4 系列
- GPT-3.5 系列
- 其他通用对话模型

### LLM_CONFIG2（代码专家模型）
**使用场景：**
- 💻 命令生成（自然语言→终端命令）
- 📝 代码编写（生成Python/Shell脚本等）
- 🔧 多步骤任务规划（涉及代码的复杂任务）

**推荐模型：**
- Claude 3.5 Sonnet（代码能力强）
- DeepSeek Coder（专门的代码模型）
- GPT-4（全能）

## 📝 配置文件

### terminal_agent_demo.py

```python
# 通用LLM配置 - 用于意图分析、问答等
LLM_CONFIG = {
    "model": "gpt-4.1-mini",
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "your-api-key-here",
    "temperature": 0,
}

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = {
    "model": "claude-3-5-sonnet",  # 或 deepseek-chat
    "base_url": "https://api.provider.com",
    "api_key": "your-code-llm-api-key",
    "temperature": 0,
}
```

### terminal_agent_interactive.py

配置结构相同，确保两个文件的配置保持一致。

## 🔄 代码中的使用

### 初始化

```python
# 通用LLM实例
llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
)

# 代码生成专用LLM实例
llm_code = ChatOpenAI(
    model=LLM_CONFIG2["model"],
    base_url=LLM_CONFIG2["base_url"],
    api_key=LLM_CONFIG2["api_key"],
    temperature=LLM_CONFIG2["temperature"],
)
```

### 使用示例

**使用 `llm`（通用模型）：**
```python
# 意图分析
def intent_analyzer(state):
    result = llm.invoke([HumanMessage(content=prompt)])
    ...

# 问答
def question_answerer(state):
    result = llm.invoke([HumanMessage(content=prompt)])
    ...
```

**使用 `llm_code`（代码模型）：**
```python
# 命令生成
def command_generator(state):
    result = llm_code.invoke([HumanMessage(content=prompt)])
    ...

# 多步骤规划（涉及代码）
def multi_step_planner(state):
    result = llm_code.invoke([HumanMessage(content=prompt)])
    ...
```

## 🎨 配置选项

### 方案一：相同模型（简化版）

如果只有一个API或想简化，两个配置可以使用相同的模型：

```python
LLM_CONFIG = {
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1",
    "api_key": "your-api-key",
    "temperature": 0,
}

LLM_CONFIG2 = LLM_CONFIG  # 使用相同配置
```

### 方案二：专用模型（推荐）

使用不同模型发挥各自优势：

```python
# 通用对话 - 使用快速便宜的模型
LLM_CONFIG = {
    "model": "gpt-3.5-turbo",
    "base_url": "https://api.openai.com/v1",
    "api_key": "your-api-key",
    "temperature": 0,
}

# 代码生成 - 使用代码能力强的模型
LLM_CONFIG2 = {
    "model": "claude-3-5-sonnet",
    "base_url": "https://api.anthropic.com/v1",
    "api_key": "your-claude-api-key",
    "temperature": 0,
}
```

### 方案三：本地模型

使用本地部署的模型（如Ollama）：

```python
LLM_CONFIG = {
    "model": "llama3",
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
    "temperature": 0,
}

LLM_CONFIG2 = {
    "model": "codellama",  # 代码专用模型
    "base_url": "http://localhost:11434/v1",
    "api_key": "not-needed",
    "temperature": 0,
}
```

## 🔧 修改配置

### 步骤1：找到配置文件

```bash
cd /Users/zhangyanhua/Desktop/AI/tushare/quantification/example
```

### 步骤2：编辑配置

编辑 `terminal_agent_demo.py` 和 `terminal_agent_interactive.py`，修改对应的配置部分。

### 步骤3：测试

```bash
# 测试Demo版本
python3 terminal_agent_demo.py

# 测试交互式版本
python3 terminal_agent_interactive.py
```

## 💡 最佳实践

### 1. 选择合适的模型

- **快速响应**：使用轻量级模型（如gpt-3.5-turbo）处理意图分析
- **准确代码**：使用代码专精模型（如Claude 3.5 Sonnet）生成命令
- **成本控制**：通用任务用便宜模型，代码生成用强力模型

### 2. Temperature设置

```python
# 意图分析和命令生成 - 需要确定性输出
temperature: 0

# 创意代码编写 - 可以适当提高
temperature: 0.2-0.5
```

### 3. 错误处理

如果某个模型API不可用，可以快速切换：

```python
# 临时回退方案
LLM_CONFIG2 = LLM_CONFIG  # 使用相同的通用模型
```

## 🐛 常见问题

### Q: API Key无效怎么办？

**A:** 检查API Key是否正确，是否有权限访问指定模型。

### Q: 能否只使用一个模型？

**A:** 可以，将 `LLM_CONFIG2 = LLM_CONFIG` 即可使用相同配置。

### Q: 代码生成效果不好？

**A:** 尝试切换到代码能力更强的模型，如：
- Claude 3.5 Sonnet
- GPT-4
- DeepSeek Coder

### Q: 成本太高怎么办？

**A:** 考虑：
- 通用任务用便宜模型（如gpt-3.5-turbo）
- 只在代码生成时用强力模型
- 使用本地开源模型

## 📊 模型对比

| 模型 | 代码能力 | 对话能力 | 速度 | 成本 |
|------|---------|---------|------|------|
| GPT-4 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 💰💰💰 |
| Claude 3.5 Sonnet | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 💰💰💰 |
| GPT-3.5-turbo | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 |
| DeepSeek Coder | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 💰 |

## 🎯 推荐组合

### 组合1：高性能（推荐）
```
LLM_CONFIG: GPT-4.1-mini (快速意图理解)
LLM_CONFIG2: Claude 3.5 Sonnet (强大代码生成)
```

### 组合2：经济实惠
```
LLM_CONFIG: GPT-3.5-turbo (通用对话)
LLM_CONFIG2: DeepSeek Coder (专精代码)
```

### 组合3：本地部署
```
LLM_CONFIG: Llama 3 (本地通用)
LLM_CONFIG2: CodeLlama (本地代码)
```

---

**更新时间：** 2025-10-21  
**版本：** 2.0 - 双LLM支持
