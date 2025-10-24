# 📂 打开目录功能

## 🎯 功能概述

AI智能体现在支持**打开目录**功能！用户可以通过自然语言请求打开当前目录或文件夹，系统会自动生成适合当前操作系统的命令。

## 🚀 支持的命令

### 中文命令
- "打开当前目录" - 打开工作目录本身
- "打开文件夹" - 打开工作目录本身  
- "打开当前文件所在目录" - 打开工作目录本身
- "在新的终端打开当前目录"
- "用文件管理器打开"
- "在Finder中打开"（macOS）
- "在资源管理器中打开"（Windows）

### 英文命令
- "open current directory"
- "open this folder"
- "open in file manager"
- "open in explorer"

## 🖥️ 不同操作系统的命令

### Windows
- **打开当前目录**: `explorer .`
- **打开文件夹**: `explorer .`
- **新终端打开**: `start cmd /k "cd /d %cd%"`
- **文件管理器**: `explorer .`

### macOS
- **打开当前目录**: `open .`
- **打开文件夹**: `open .`
- **新终端打开**: `open -a Terminal .`
- **文件管理器**: `open .`

### Linux
- **打开当前目录**: `xdg-open .` 或 `nautilus .`
- **打开文件夹**: `xdg-open .` 或 `nautilus .`
- **新终端打开**: `gnome-terminal --working-directory=.`
- **文件管理器**: `xdg-open .`

## 📋 使用示例

```bash
./ai-agent
👤 你: 打开当前文件所在目录

🤖 执行命令: 打开当前文件所在目录

[意图分析] 打开当前文件所在目录...
           意图: terminal_command

[命令生成] open .
           使用模型: gpt-4o-mini
           操作系统: Darwin

[执行命令] open .
[执行成功] 输出长度: 0 字符

✅ 命令执行成功

命令: open .

输出:
(命令执行成功，无输出)
```

## 🔧 技术实现

### 1. 工具选择优先级
在 `simple_tool_calling_node` 函数中添加了打开目录的优先检测：

```python
# 先检查是否是打开目录的请求
user_input_lower = user_input.lower()
open_keywords = ["打开", "open"]
directory_keywords = ["目录", "文件夹", "终端", "directory", "folder", "finder", "explorer", "文件管理器", "资源管理器"]

has_open = any(kw in user_input_lower for kw in open_keywords)
has_directory = any(kw in user_input_lower for kw in directory_keywords)

# 如果是打开目录请求，直接返回terminal_command意图
if has_open and has_directory:
    return {"intent": "terminal_command", "response": ""}
```

### 2. 意图识别增强
在 `intent_analyzer` 函数中添加了打开目录的识别规则：

```python
5. 终端命令 (terminal_command) - 执行系统命令
   关键特征：包含"打开"、"目录"、"文件夹"、"终端"等操作词汇
   示例：
   - "打开当前文件所在目录"
   - "在新的终端打开当前目录"
   - "打开这个文件夹"
   - "用文件管理器打开"
   - "在Finder中打开"
   - "在资源管理器中打开"
```

### 3. 命令生成
在 `command_generator` 函数中为不同操作系统添加了打开目录的命令示例：

**Windows示例**:
```
- "打开当前目录" -> explorer .
- "在新的终端打开当前目录" -> start cmd /k "cd /d %cd%"
```

**macOS/Linux示例**:
```
- "打开当前目录" -> open .
- "在新的终端打开当前目录" -> open -a Terminal .
```

## 🎯 工作流程

1. **用户输入** → 用户说出打开目录的请求
2. **优先检测** → `simple_tool_calling_node` 检测到打开目录关键词
3. **意图路由** → 直接返回 `terminal_command` 意图，跳过MCP工具选择
4. **命令生成** → `command_generator` 根据操作系统生成对应命令
5. **命令执行** → `command_executor` 执行生成的系统命令
6. **结果反馈** → 显示执行结果

### 关键改进
- **避免误识别**: 不会被误认为MCP文件系统工具（如fs_list）
- **优先级处理**: 在工具选择阶段就直接识别，提高准确性
- **双重保障**: 既有工具选择层面的检测，也有意图分析层面的规则

## 💡 注意事项

- 命令会在当前工作目录执行
- 不同操作系统使用不同的文件管理器
- 如果系统没有安装对应的文件管理器，命令可能失败
- 在某些受限环境（如沙盒）中，打开GUI应用可能受限

## 🔍 故障排除

### 命令执行失败
如果打开目录命令失败，可能的原因：
1. 系统没有安装对应的文件管理器
2. 当前环境不支持GUI应用
3. 权限不足

### 解决方案
- Windows: 确保 `explorer.exe` 可用
- macOS: 确保 Finder 正常工作
- Linux: 安装 `xdg-utils` 或对应的文件管理器

## 🚀 扩展功能

未来可以考虑添加：
- 打开指定路径的目录
- 在特定应用中打开目录
- 支持更多文件管理器
- 批量打开多个目录

---

*该功能已集成到AI智能体的核心工作流中，无需额外配置即可使用。*
