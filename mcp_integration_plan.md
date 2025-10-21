# 🔌 MCP集成方案

## 📋 需求分析

### 什么是MCP？
**Model Context Protocol (模型上下文协议)** 是一个开放标准协议，用于连接AI应用与外部数据源和工具。

### MCP的核心概念

1. **MCP Server（MCP服务器）**
   - 提供工具和资源的后端服务
   - 例如：文件系统访问、数据库查询、API调用等

2. **MCP Client（MCP客户端）**
   - AI应用端，连接并使用MCP服务器
   - 通过协议调用服务器提供的工具

3. **Tools（工具）**
   - 服务器暴露的功能
   - LLM可以调用这些工具完成任务

4. **Resources（资源）**
   - 服务器提供的数据源
   - 例如：文件内容、数据库记录等

---

## 🎯 集成目标

### 为什么要集成MCP？

1. **扩展能力**
   - 访问文件系统
   - 连接数据库
   - 调用外部API
   - 读取网页内容

2. **标准化接口**
   - 使用统一的协议
   - 易于添加新工具
   - 模块化设计

3. **安全隔离**
   - 工具运行在独立服务器
   - 可控的权限管理

---

## 🏗️ 集成方案

### 方案A：使用官方MCP Python SDK

#### 优点
✅ 官方支持，稳定可靠  
✅ 完整的协议实现  
✅ 良好的文档

#### 缺点
❌ 需要安装额外依赖  
❌ 学习曲线较陡

#### 实现步骤
```bash
# 1. 安装MCP SDK
pip install mcp

# 2. 配置MCP服务器
# 3. 在LangGraph中集成MCP工具
# 4. 测试工具调用
```

---

### 方案B：使用LangChain的MCP集成

#### 优点
✅ 与现有LangChain代码无缝集成  
✅ 简化开发  
✅ 自动工具转换

#### 缺点
❌ 可能功能受限  
❌ 依赖LangChain生态

---

### 方案C：自定义轻量级MCP实现

#### 优点
✅ 完全可控  
✅ 轻量级  
✅ 针对性优化

#### 缺点
❌ 需要自己实现协议  
❌ 维护成本高

---

## 💡 推荐方案：方案B（LangChain + MCP）

### 架构设计

```
用户输入
    ↓
意图分析 [LLM]
    ↓
    ├─ 需要工具? → MCP客户端 → MCP服务器
    │                ↓            ↓
    │           调用工具     执行操作
    │                ↓            ↓
    │           返回结果 ← ← ← ← ←
    │                ↓
    └─ 生成响应 [LLM]
         ↓
    显示结果
```

---

## 🛠️ 可用的MCP服务器

### 1. **filesystem** - 文件系统访问
```
功能：
- 读取文件内容
- 写入文件
- 列出目录
- 搜索文件
```

### 2. **sqlite** - SQLite数据库
```
功能：
- 执行SQL查询
- 读取表结构
- 插入/更新数据
```

### 3. **fetch** - HTTP请求
```
功能：
- GET/POST请求
- 下载网页
- API调用
```

### 4. **github** - GitHub集成
```
功能：
- 读取仓库
- 创建Issue
- PR管理
```

### 5. **memory** - 持久化记忆
```
功能：
- 保存知识
- 检索记忆
- 更新上下文
```

---

## 📝 实现计划

### 阶段1：基础集成（第1天）
- [ ] 安装MCP依赖
- [ ] 配置filesystem MCP服务器
- [ ] 实现MCP客户端连接
- [ ] 测试基础工具调用

### 阶段2：LangGraph集成（第2天）
- [ ] 将MCP工具转换为LangChain工具
- [ ] 在工作流中添加工具调用节点
- [ ] 实现智能工具选择
- [ ] 测试端到端流程

### 阶段3：功能扩展（第3天）
- [ ] 添加更多MCP服务器
- [ ] 优化工具调用逻辑
- [ ] 添加工具调用日志
- [ ] 完善错误处理

### 阶段4：用户体验（第4天）
- [ ] 优化显示输出
- [ ] 添加工具使用说明
- [ ] 编写使用文档
- [ ] 完整测试

---

## 🎨 用户体验设计

### 示例1：文件操作
```
👤 你: 读取当前目录下的README.md文件

[意图分析] 使用模型: kimi-k2-0905-preview
           意图: tool_call

[工具选择] filesystem.read_file
           MCP服务器: filesystem
           
[工具执行] 读取文件: README.md
           ✅ 成功

🤖 助手: 已读取README.md文件内容：
[文件内容...]
```

### 示例2：数据库查询
```
👤 你: 查询数据库中所有用户

[意图分析] 使用模型: kimi-k2-0905-preview
           意图: tool_call

[工具选择] sqlite.query
           MCP服务器: sqlite
           
[工具执行] SQL: SELECT * FROM users
           ✅ 返回5条记录

🤖 助手: 查询结果：
1. 用户A - admin@example.com
2. 用户B - user@example.com
...
```

### 示例3：组合操作
```
👤 你: 读取data.csv，统计总数，然后保存到result.txt

[意图分析] 使用模型: kimi-k2-0905-preview
           意图: multi_step_tool_call

[多步骤规划] 使用模型: claude-3-5-sonnet
            工具序列: 
            1. filesystem.read_file(data.csv)
            2. [处理数据]
            3. filesystem.write_file(result.txt)

[工具执行]
  ✅ 步骤1: 读取data.csv (100行)
  ✅ 步骤2: 统计完成 (总数: 1234)
  ✅ 步骤3: 保存到result.txt

🤖 助手: 已完成数据统计并保存：
- 读取记录: 100条
- 统计总数: 1234
- 结果已保存到: result.txt
```

---

## 🔧 技术实现

### 1. 安装依赖
```bash
pip install mcp
pip install langchain-mcp  # 如果有的话
```

### 2. 配置MCP服务器
```json
// mcp_config.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"]
    }
  }
}
```

### 3. 初始化MCP客户端
```python
from mcp import Client, StdioServerParameters
from langchain.tools import Tool

class MCPManager:
    def __init__(self):
        self.clients = {}
        self.tools = []
    
    async def connect_server(self, name, config):
        """连接MCP服务器"""
        params = StdioServerParameters(
            command=config["command"],
            args=config["args"]
        )
        client = Client()
        await client.connect(params)
        self.clients[name] = client
        
        # 获取工具列表
        tools = await client.list_tools()
        for tool in tools:
            self.tools.append(self._convert_to_langchain_tool(tool))
    
    def _convert_to_langchain_tool(self, mcp_tool):
        """转换MCP工具为LangChain工具"""
        def tool_func(*args, **kwargs):
            # 调用MCP工具
            return self._call_mcp_tool(mcp_tool, *args, **kwargs)
        
        return Tool(
            name=mcp_tool.name,
            description=mcp_tool.description,
            func=tool_func
        )
```

### 4. 工作流集成
```python
# 添加工具调用节点
workflow.add_node("call_tools", tool_executor)

# 添加工具选择路由
def route_with_tools(state):
    if state["needs_tools"]:
        return "call_tools"
    else:
        return "format_response"
```

---

## 🎯 优先实现的MCP服务器

### 1. filesystem（优先级：高）
**原因：** 最常用，与终端控制结合紧密

**功能：**
- 读取文件
- 写入文件
- 列出目录
- 搜索内容

### 2. fetch（优先级：中）
**原因：** 扩展网络能力

**功能：**
- 下载网页
- API调用
- 获取在线资源

### 3. sqlite（优先级：中）
**原因：** 数据持久化

**功能：**
- 查询数据
- 存储结果
- 数据分析

---

## 📊 预期效果

### 功能增强
- ✅ 可以读写文件
- ✅ 可以查询数据库
- ✅ 可以调用API
- ✅ 可以执行复杂任务流

### 用户体验
- ✅ 更强大的能力
- ✅ 统一的交互方式
- ✅ 清晰的执行日志
- ✅ 智能的工具选择

---

## ❓ 需要确认的问题

### 请回答以下问题，帮助我设计最合适的方案：

1. **你想使用哪些MCP功能？**
   - [ ] 文件系统访问
   - [ ] 数据库操作
   - [ ] 网络请求
   - [ ] GitHub集成
   - [ ] 其他：___________

2. **你的使用场景是什么？**
   - 数据分析？
   - 文件处理？
   - API集成？
   - 自动化任务？

3. **是否需要持久化记忆？**
   - 是 / 否

4. **是否需要网络访问能力？**
   - 是 / 否

5. **是否有特定的MCP服务器需求？**
   - 请描述：___________

---

## 📝 下一步

请告诉我：
1. 你最需要哪些MCP功能
2. 你的主要使用场景
3. 是否有特殊需求

我会根据你的回答设计最合适的集成方案并开始实现。

---

**文档版本：** 1.0  
**创建时间：** 2025-10-21  
**状态：** 等待需求确认
