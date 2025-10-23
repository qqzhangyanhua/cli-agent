# @ 文件引用功能升级指南

## 🎉 新功能亮点

已成功将 @ 文件引用功能升级为类似 **Codex/Claude Code** 的 IDE 风格体验！

### 主要改进

| 旧版本 | 新版本 |
|--------|--------|
| ❌ 需要单独输入 `@` 启动选择器 | ✅ 输入 `@` 后立即自动补全 |
| ❌ 全屏模式切换，打断输入流程 | ✅ 内联补全，流畅输入 |
| ❌ 需要多步操作选择文件 | ✅ 实时过滤，上下选择即可 |
| ❌ 无历史记录 | ✅ 智能历史记录和建议 |
| ❌ 固定列表显示 | ✅ 模糊搜索，智能排序 |

## 🚀 快速开始

### 1. 安装依赖

为了获得最佳体验，请安装 `prompt-toolkit`：

```bash
pip install prompt-toolkit>=3.0.0
```

### 2. 验证安装

```bash
python -c "import prompt_toolkit; print('✅ 已安装')"
```

### 3. 开始使用

```bash
# 启动交互模式
dnm

# 或
ai-agent
```

## 💡 使用示例

### 基础用法 - 自动补全

```
👤 你: @
```

当你输入 `@` 后，会立即看到文件列表弹出：

```
📁 agent_config.py (3.2K)
📁 agent_workflow.py (8.5K)
📝 README.md (12.3K)
...
```

继续输入过滤：

```
👤 你: @read
```

自动过滤显示匹配的文件：

```
📝 README.md (12.3K)
📝 README_INTERACTIVE.md (5.1K)
```

使用 `↑` `↓` 选择，按 `Enter` 确认。

### 完整对话示例

```
👤 你: @README.md 总结这个项目
🤖 助手: 这是一个 AI 智能体终端控制工具...

👤 你: 比较 @agent_config.py 和 @agent_llm.py
🤖 助手: agent_config.py 负责配置管理...

👤 你: @test/test_demo.py 这个测试文件是做什么的？
🤖 助手: 这是一个演示测试文件...
```

### 模糊搜索

```
👤 你: @cfg      → 匹配 agent_config.py
👤 你: @wkf      → 匹配 agent_workflow.py  
👤 你: @ui       → 匹配 agent_ui.py
👤 你: @test/demo → 匹配 test/test_demo.py
```

## 🎯 快捷键

在输入时可使用以下快捷键：

| 快捷键 | 功能 |
|--------|------|
| `↑` | 上一个补全选项 |
| `↓` | 下一个补全选项 |
| `Tab` | 补全当前选中项 |
| `Enter` | 确认选择 |
| `Ctrl+C` | 取消输入 |
| `↑` (历史) | 浏览上一条历史命令 |
| `↓` (历史) | 浏览下一条历史命令 |

## 🔄 降级模式

如果 `prompt-toolkit` 未安装，系统会自动降级到传统模式：

### 传统模式特性

- 输入单独的 `@` 启动全屏文件选择器
- 输入 `@文件名` 触发快速搜索
- 支持分页浏览和过滤

### 传统模式示例

```
👤 你: @
🎯 启动文件选择器...

[全屏文件列表显示]
• 输入数字选择文件
• 输入文件名搜索
• 'n' 下一页, 'p' 上一页
• 'q' 退出
```

## 📊 对比演示

### 旧版本操作流程

```
1. 输入: @
2. 等待全屏选择器启动
3. 浏览文件列表
4. 输入搜索词: readme
5. 输入数字选择: 1
6. 返回输入: 总结这个文档
```
**共需 6 步操作** ❌

### 新版本操作流程

```
1. 输入: @read [自动显示匹配]
2. 按 ↓ 选择 README.md，Enter 确认
3. 继续输入: 总结这个文档
```
**只需 2-3 步操作** ✅

## 🎨 文件图标

新版本支持丰富的文件类型图标：

- 🐍 Python (`.py`)
- 🟨 JavaScript (`.js`, `.jsx`)
- 🔷 TypeScript (`.ts`, `.tsx`)
- 📝 Markdown (`.md`)
- 📋 JSON (`.json`)
- ⚙️ YAML (`.yml`, `.yaml`)
- 🌐 HTML (`.html`)
- 🎨 CSS (`.css`, `.scss`)
- 📁 目录
- 📄 其他文本文件

## 🔧 高级配置

### 调整扫描深度

编辑 `smart_file_input.py`：

```python
def _scan_directory(self, directory: Path, depth: int = 0, max_depth: int = 5):
    # 将 max_depth 从 3 改为 5，扫描更深的目录
```

### 调整补全结果数量

```python
# 限制结果数量
matches = matches[:30]  # 默认 20，可改为 30
```

### 自定义历史文件位置

```python
smart_input = SmartFileInput(
    working_dir="/path/to/project",
    history_file="/path/to/custom_history"
)
```

## 📝 文档

详细文档请参阅：
- [docs/SMART_FILE_REFERENCE.md](docs/SMART_FILE_REFERENCE.md) - 完整功能文档
- [test_smart_file_input.py](test_smart_file_input.py) - 测试和示例

## 🐛 故障排除

### 问题 1: 自动补全不工作

**症状**: 输入 `@` 后没有弹出补全列表

**解决方案**:
```bash
# 1. 检查是否已安装
python -c "import prompt_toolkit"

# 2. 如果未安装
pip install prompt-toolkit

# 3. 如果仍有问题，查看错误信息
python test_smart_file_input.py
```

### 问题 2: 补全列表不完整

**症状**: 某些文件没有显示在补全列表中

**可能原因**:
- 文件在被忽略的目录中（如 `node_modules/`, `.git/`）
- 扫描深度限制（默认 3 层）

**解决方案**: 调整 `max_depth` 参数

### 问题 3: Windows 中文显示问题

**症状**: 文件名中的中文显示为乱码

**解决方案**:
```bash
# 设置控制台编码为 UTF-8
chcp 65001
```

或在 PowerShell 中：
```powershell
$OutputEncoding = [System.Text.Encoding]::UTF8
```

## 🔄 回退到旧版本

如果遇到问题需要回退：

```bash
# 1. 卸载 prompt-toolkit
pip uninstall prompt-toolkit

# 2. 系统会自动使用降级模式（传统选择器）
```

## ✨ 下一步

尝试以下高级功能：

1. **多文件引用**
   ```
   👤 你: 比较 @old.txt 和 @new.txt 的差异
   ```

2. **目录操作**
   ```
   👤 你: 列出 @docs/ 目录下的所有文件
   ```

3. **结合其他功能**
   ```
   👤 你: @data.json 转换为 CSV 格式
   👤 你: @test.py 进行代码审查
   ```

## 📞 反馈

如有问题或建议，欢迎反馈！

---

**版本**: 1.0.0  
**日期**: 2025-10-22  
**作者**: CLI Agent Team

