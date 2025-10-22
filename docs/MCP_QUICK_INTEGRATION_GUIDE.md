# 🚀 MCP快速集成指南

## ✅ 已完成的工作

### 1. 创建的文件

| 文件 | 大小 | 说明 |
|------|------|------|
| **mcp_config.json** | - | MCP服务器配置（desktop-commander） |
| **mcp_filesystem.py** | 15.4KB | 文件系统工具模块 ✅ 测试通过 |
| **mcp_manager.py** | 9.2KB | MCP管理器 ✅ 测试通过 |
| **test_mcp_integration.py** | 4.8KB | MCP测试脚本 ✅ 全部通过 |

### 2. 可用的MCP工具

#### 📁 文件系统工具（5个）
```python
from mcp_manager import mcp_manager

# 读取文件
mcp_manager.call_tool("fs_read", file_path="README.md", max_lines=100)

# 写入文件
mcp_manager.call_tool("fs_write", file_path="output.txt", content="内容")

# 列出目录
mcp_manager.call_tool("fs_list", dir_path=".", pattern="*.py")

# 搜索文件
mcp_manager.call_tool("fs_search", dir_path=".", filename_pattern="*.md")

# 获取文件信息
mcp_manager.call_tool("fs_info", file_path="script.py")
```

#### 🖥️ 桌面控制工具（4个）
```python
# 执行桌面命令
mcp_manager.call_tool("desktop_execute", command="echo hello")

# 截图
mcp_manager.call_tool("desktop_screenshot", output_path="screenshot.png")

# 读取剪贴板
mcp_manager.call_tool("desktop_read_clipboard")

# 写入剪贴板
mcp_manager.call_tool("desktop_write_clipboard", text="Hello World")
```

---

## 🔧 如何集成到terminal_agent_interactive.py

### 步骤1: 添加导入
```python
from mcp_manager import mcp_manager
```

### 步骤2: 扩展AgentState
```python
class AgentState(TypedDict):
    # ... 现有字段 ...
    # 新增MCP字段
    intent: Literal["terminal_command", "multi_step_command", "mcp_tool_call", "question", "unknown"]
    mcp_tool: str
    mcp_params: dict
    mcp_result: str
```

### 步骤3: 修改意图分析
在 `intent_analyzer()` 的prompt中添加：
```python
判断规则:
- 如果用户想读写文件、列出目录、搜索文件 -> mcp_tool_call
- 如果用户想截图、操作剪贴板 -> mcp_tool_call
- 如果用户想执行系统命令 -> terminal_command
- ...
```

### 步骤4: 添加MCP工具规划节点
```python
def mcp_tool_planner(state: AgentState) -> dict:
    """规划MCP工具调用"""
    user_input = state["user_input"]
    
    # 获取可用工具列表
    available_tools = mcp_manager.list_available_tools()
    tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in available_tools])
    
    prompt = f"""分析用户请求，选择合适的MCP工具并返回JSON格式。

可用工具:
{tools_desc}

用户请求: {user_input}

返回JSON:
{{
  "tool": "工具名称",
  "params": {{参数}}
}}

示例:
输入: "读取README.md文件"
输出: {{
  "tool": "fs_read",
  "params": {{"file_path": "README.md"}}
}}

只返回JSON:"""
    
    result = llm_code.invoke([HumanMessage(content=prompt)])
    plan_text = result.content.strip()
    
    # 提取JSON
    if "```json" in plan_text:
        plan_text = plan_text.split("```json")[1].split("```")[0].strip()
    elif "```" in plan_text:
        plan_text = plan_text.split("```")[1].split("```")[0].strip()
    
    try:
        plan = json.loads(plan_text)
        print(f"[MCP工具规划] 使用模型: {LLM_CONFIG2['model']}")
        print(f"            工具: {plan.get('tool', 'unknown')}")
        
        return {
            "mcp_tool": plan.get("tool", ""),
            "mcp_params": plan.get("params", {})
        }
    except json.JSONDecodeError:
        return {
            "mcp_tool": "",
            "mcp_params": {},
            "error": "无法解析MCP工具规划"
        }
```

### 步骤5: 添加MCP工具执行节点
```python
def mcp_tool_executor(state: AgentState) -> dict:
    """执行MCP工具"""
    tool_name = state["mcp_tool"]
    params = state["mcp_params"]
    
    print(f"[MCP工具执行] 工具: {tool_name}")
    print(f"            参数: {params}")
    
    try:
        result = mcp_manager.call_tool(tool_name, **params)
        
        if result.get("success"):
            print(f"[MCP工具执行] ✅ 成功")
        else:
            print(f"[MCP工具执行] ❌ 失败: {result.get('error')}")
        
        return {"mcp_result": json.dumps(result, ensure_ascii=False)}
    
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        print(f"[MCP工具执行] ❌ 异常: {e}")
        return {"mcp_result": json.dumps(error_result, ensure_ascii=False)}
```

### 步骤6: 更新response_formatter
```python
def response_formatter(state: AgentState) -> dict:
    """格式化最终响应"""
    # ... 现有代码 ...
    
    elif state["intent"] == "mcp_tool_call":
        result = json.loads(state.get("mcp_result", "{}"))
        
        if result.get("success"):
            response = f"✅ MCP工具执行成功\n\n"
            response += f"工具: {state['mcp_tool']}\n"
            
            # 根据不同工具类型格式化输出
            if state['mcp_tool'] == "fs_read":
                response += f"内容:\n{result['content'][:500]}..."
            elif state['mcp_tool'] == "fs_list":
                response += f"找到 {result['total_files']} 个文件\n"
                for f in result['files'][:10]:
                    response += f"  • {f['name']} ({f['size_human']})\n"
            elif state['mcp_tool'] == "fs_search":
                response += f"找到 {result['total']} 个匹配文件\n"
                for f in result['matches'][:10]:
                    response += f"  • {f['name']}\n"
            else:
                response += f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            response = f"❌ MCP工具执行失败\n\n"
            response += f"工具: {state['mcp_tool']}\n"
            response += f"错误: {result.get('error')}"
    
    # ... 其余代码 ...
```

### 步骤7: 更新工作流
```python
def build_agent() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # 添加MCP节点
    workflow.add_node("plan_mcp_tool", mcp_tool_planner)
    workflow.add_node("execute_mcp_tool", mcp_tool_executor)
    
    # 更新路由
    def route_by_intent(state: AgentState) -> str:
        intent = state["intent"]
        if intent == "terminal_command":
            return "generate_command"
        elif intent == "multi_step_command":
            return "plan_steps"
        elif intent == "mcp_tool_call":  # 新增
            return "plan_mcp_tool"
        elif intent == "question":
            return "answer_question"
        else:
            return "format_response"
    
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "plan_mcp_tool": "plan_mcp_tool",  # 新增
            "answer_question": "answer_question",
            "format_response": "format_response"
        }
    )
    
    # MCP工具路径
    workflow.add_edge("plan_mcp_tool", "execute_mcp_tool")
    workflow.add_edge("execute_mcp_tool", "format_response")
    
    # ... 其余路径 ...
    
    return workflow.compile()
```

### 步骤8: 更新欢迎信息
```python
def print_header():
    print("\n🔧 MCP功能:")
    print(f"  • 文件系统: 读取/写入/列出/搜索文件")
    print(f"  • 桌面控制: 截图/剪贴板/执行命令")
    
    # 显示可用工具数量
    tools = mcp_manager.list_available_tools()
    fs_tools = [t for t in tools if t['type'] == 'filesystem']
    desktop_tools = [t for t in tools if t['type'] == 'desktop-commander']
    print(f"  • 已加载: {len(fs_tools)}个文件工具, {len(desktop_tools)}个桌面工具")
```

### 步骤9: 添加'tools'特殊命令
```python
def handle_special_commands(user_input: str) -> bool:
    # ... 现有命令 ...
    
    if user_input_lower in ['tools', '工具']:
        print("\n🛠️ 可用的MCP工具:")
        print("─" * 80)
        tools = mcp_manager.list_available_tools()
        
        for tool_type in ['filesystem', 'desktop-commander']:
            type_tools = [t for t in tools if t['type'] == tool_type]
            if type_tools:
                icon = "📁" if tool_type == "filesystem" else "🖥️"
                print(f"\n{icon} {tool_type} ({len(type_tools)}个):")
                for t in type_tools:
                    print(f"   • {t['name']:25} - {t['description']}")
        
        print("─" * 80 + "\n")
        return False
```

### 步骤10: 更新初始状态
```python
initial_state: AgentState = {
    "user_input": user_input,
    "intent": "unknown",
    "command": "",
    "commands": [],
    "command_output": "",
    "command_outputs": [],
    "response": "",
    "error": "",
    "needs_file_creation": False,
    "file_path": "",
    "file_content": "",
    "chat_history": [],
    # MCP字段
    "mcp_tool": "",
    "mcp_params": {},
    "mcp_result": ""
}
```

---

## 🧪 测试示例

集成完成后，你可以这样使用：

```
👤 你: 读取README.md文件

[意图分析] 使用模型: kimi-k2-0905-preview
           意图: mcp_tool_call
[MCP工具规划] 使用模型: claude-3-5-sonnet
            工具: fs_read
[MCP工具执行] 工具: fs_read
[MCP工具执行] ✅ 成功

🤖 助手: ✅ MCP工具执行成功

工具: fs_read
内容:
# AI智能终端助手
...

👤 你: 列出当前目录的所有Python文件

[意图分析] 意图: mcp_tool_call
[MCP工具规划] 工具: fs_list
[MCP工具执行] ✅ 成功

🤖 助手: ✅ MCP工具执行成功

工具: fs_list
找到 8 个文件
  • lang.py (5.0KB)
  • mcp_manager.py (9.2KB)
  ...

👤 你: tools

🛠️ 可用的MCP工具:
────────────────────────────────────────────────

📁 filesystem (5个):
   • fs_read       - 读取文件内容
   • fs_write      - 写入文件内容
   • fs_list       - 列出目录内容
   • fs_search     - 搜索文件
   • fs_info       - 获取文件信息

🖥️ desktop-commander (4个):
   • desktop_execute           - 执行桌面命令或脚本
   • desktop_screenshot        - 截取屏幕截图
   • desktop_read_clipboard    - 读取剪贴板内容
   • desktop_write_clipboard   - 写入剪贴板内容
```

---

## 📝 完整集成checklist

- [ ] 步骤1: 添加导入
- [ ] 步骤2: 扩展AgentState
- [ ] 步骤3: 修改意图分析
- [ ] 步骤4: 添加mcp_tool_planner节点
- [ ] 步骤5: 添加mcp_tool_executor节点
- [ ] 步骤6: 更新response_formatter
- [ ] 步骤7: 更新工作流build_agent()
- [ ] 步骤8: 更新print_header()
- [ ] 步骤9: 添加'tools'特殊命令
- [ ] 步骤10: 更新初始状态

---

## 🎯 快速集成命令

由于文件较长，建议分步骤手动集成，或者使用我提供的完整示例文件。

如果需要完整的集成文件，可以参考：
- `terminal_agent_mcp.py` （之前创建的完整示例）

---

## ✅ 现有功能

目前MCP功能已经完全ready，你可以：

### 方式1: 直接使用MCP管理器
```python
from mcp_manager import mcp_manager

# 文件操作
result = mcp_manager.call_tool("fs_read", file_path="README.md")
result = mcp_manager.call_tool("fs_list", dir_path=".", pattern="*.py")

# 桌面操作（需要desktop-commander运行）
result = mcp_manager.call_tool("desktop_screenshot")
```

### 方式2: 测试脚本
```bash
python3 test_mcp_integration.py  # 测试文件系统工具
python3 mcp_manager.py           # 测试MCP管理器
```

---

## 🚀 下一步

1. **手动集成**：按照上述10个步骤修改 `terminal_agent_interactive.py`
2. **使用示例**：参考 `terminal_agent_mcp.py` 中的完整实现
3. **测试验证**：集成后测试文件操作和桌面控制功能

---

**文档版本：** 1.0  
**创建时间：** 2025-10-21  
**状态：** MCP核心功能完成，集成指南ready
