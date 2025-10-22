# 智能文件引用功能升级 - IDE 风格体验

## 概述

新的 @ 文件引用功能采用了类似 Codex/Claude Code 的 IDE 风格体验，提供实时自动补全和模糊搜索。

## 核心特性

### 🎯 实时自动补全
- 输入 `@` 后立即显示文件列表（无需额外操作）
- 继续输入时实时过滤和匹配
- 类似 IDE 的下拉菜单体验

### 🔍 智能搜索
- **精确匹配** (100分): 文件名完全匹配
- **前缀匹配** (90分): 文件名以输入开头
- **包含匹配** (70分): 文件名包含输入内容
- **模糊匹配** (50分): 字符按顺序出现

### 📂 文件信息展示
- 📁 文件图标（根据类型显示）
- 📍 相对路径显示
- 📏 文件大小显示
- 🎨 语法高亮（路径中的图标）

### ⌨️ 快捷操作
- `↑` `↓` 上下选择文件
- `Tab` 补全当前选中项
- `Enter` 确认选择
- `Ctrl+C` 取消输入

### 📝 历史记录
- 自动保存输入历史
- `↑` `↓` 浏览历史命令
- 基于历史的智能建议

## 使用示例

### 基础用法

```bash
# 启动交互模式
dnm

# 输入 @ 后立即显示文件列表
👤 你: @

# 继续输入进行过滤
👤 你: @read

# 显示匹配结果：
#   🐍 README.md (2.5K)
#   📝 README_INTERACTIVE.md (3.1K)
#   📋 requirements.txt (1.2K)

# 使用上下箭头选择，按 Enter 确认
👤 你: @README.md 这个项目是做什么的？
```

### 多文件引用

```bash
# 引用多个文件
👤 你: 比较 @agent_config.py 和 @agent_llm.py 的差异
```

### 路径引用

```bash
# 相对路径
👤 你: @./docs/README.md 总结这个文档

# 子目录文件
👤 你: @test/test_demo.py 解释这个测试文件
```

### 模糊搜索

```bash
# 输入部分字符即可匹配
👤 你: @wkf  # 匹配 agent_workflow.py
👤 你: @cfg  # 匹配 agent_config.py
👤 你: @ui   # 匹配 agent_ui.py
```

## 文件图标映射

| 文件类型 | 图标 | 示例 |
|---------|------|------|
| Python  | 🐍 | `.py` |
| JavaScript | 🟨 | `.js`, `.jsx` |
| TypeScript | 🔷 | `.ts`, `.tsx` |
| Markdown | 📝 | `.md` |
| JSON | 📋 | `.json` |
| YAML | ⚙️ | `.yml`, `.yaml` |
| HTML | 🌐 | `.html` |
| CSS | 🎨 | `.css` |
| 图片 | 🖼️ | `.jpg`, `.png` |
| 目录 | 📁 | - |

## 降级模式

如果 `prompt-toolkit` 未安装或出现错误，系统会自动降级到传统的文件选择模式：

### 传统模式特性
- 单独输入 `@` 启动全屏文件选择器
- 输入 `@文件名` 触发快速搜索
- 分页浏览文件列表
- 支持搜索和过滤

### 传统模式操作
```bash
# 全屏选择器
👤 你: @
# 显示交互式文件列表

# 快速搜索
👤 你: @read
# 显示匹配 "read" 的文件

# 操作提示
#   • 输入数字选择文件
#   • 输入文件名搜索
#   • 'n' 下一页, 'p' 上一页
#   • 'r' 刷新, 'h' 显示隐藏文件
#   • 'q' 退出
```

## 安装增强功能

### 自动安装
新安装的用户会自动安装 `prompt-toolkit`。

### 手动安装
如果需要手动安装：

```bash
pip install prompt-toolkit>=3.0.0
```

### 验证安装
```bash
python3 -c "import prompt_toolkit; print('✅ prompt-toolkit 已安装')"
```

## 配置选项

### 缓存深度
文件扫描深度默认为 3 层，可在 `smart_file_input.py` 中修改：

```python
def _scan_directory(self, directory: Path, depth: int = 0, max_depth: int = 3):
```

### 结果限制
自动补全结果默认显示前 20 个，可修改：

```python
# 限制结果数量
matches = matches[:20]  # 修改这个数字
```

### 历史文件
历史记录默认保存在工作目录的 `.dnm_history`，可在创建实例时指定：

```python
smart_input = SmartFileInput(history_file="/path/to/history")
```

## 性能优化

### 文件缓存
- 首次使用时扫描目录并缓存
- 缓存包含文件路径、大小、图标等信息
- 递归扫描深度限制为 3 层

### 忽略规则
自动忽略以下目录以提升性能：
- `.git/`
- `node_modules/`
- `__pycache__/`
- `venv/`
- 以 `.` 开头的隐藏文件

### 刷新缓存
如果文件系统发生变化，缓存会在下次输入 `@` 时自动刷新。

## 故障排除

### 问题：自动补全不工作
**解决方案：**
1. 检查 `prompt-toolkit` 是否已安装
2. 查看是否有错误信息提示降级模式
3. 尝试重新安装：`pip install --upgrade prompt-toolkit`

### 问题：文件列表不完整
**解决方案：**
1. 检查是否因性能限制忽略了某些目录
2. 增加 `max_depth` 参数
3. 检查文件权限

### 问题：补全速度慢
**解决方案：**
1. 减少 `max_depth` 参数
2. 减少结果显示数量
3. 添加更多目录到忽略列表

### 问题：历史记录不保存
**解决方案：**
1. 检查工作目录写权限
2. 指定其他历史文件路径
3. 禁用历史记录功能

## 技术实现

### 架构设计

```
SmartFileInput (主类)
    ├── FileCompleter (自动补全器)
    │   ├── _scan_directory() - 递归扫描文件
    │   ├── _fuzzy_match() - 模糊匹配算法
    │   ├── get_completions() - 生成补全建议
    │   └── _get_file_icon() - 文件图标映射
    │
    ├── get_input() - 增强输入（prompt_toolkit）
    └── _fallback_input() - 降级输入（传统模式）
```

### 集成方式

```python
# dnm / ai-agent 入口文件
from smart_file_input import (
    get_smart_input,
    update_smart_input_directory,
    check_prompt_toolkit_available,
)

def smart_input_handler(prompt: str = "👤 你: ") -> str:
    if check_prompt_toolkit_available():
        return get_smart_input(prompt)
    else:
        # 降级到传统模式
        ...
```

## 对比传统方式

### 传统方式
```
1. 输入 @
2. 等待全屏选择器启动
3. 浏览分页列表
4. 输入搜索词过滤
5. 输入数字选择
6. 再次输入指令
```
**需要 6 步操作**

### 新方式
```
1. 输入 @ 后继续输入文件名
2. 上下选择并回车确认
```
**只需 2 步操作**

## 未来增强

- [ ] 支持文件预览（显示前几行内容）
- [ ] 支持文件修改时间排序
- [ ] 支持按文件类型过滤
- [ ] 支持 Git 状态显示（修改、新增等）
- [ ] 支持最近使用的文件优先
- [ ] 支持收藏文件功能
- [ ] 支持正则表达式搜索

## 反馈和建议

如果你有任何建议或发现问题，欢迎反馈！

---

**最后更新**: 2025-10-22  
**版本**: 1.0.0

