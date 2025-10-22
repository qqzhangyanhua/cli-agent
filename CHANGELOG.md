# 更新日志

## [1.1.0] - 2025-10-22

### ✨ 新增

#### @ 文件引用功能全面升级

**IDE 风格自动补全体验**
- 🎯 实时自动补全：输入 `@` 后立即显示文件列表
- 🔍 智能模糊搜索：支持缩写匹配（如 `@cfg` → `agent_config.py`）
- ⌨️ 流畅键盘操作：上下箭头、Tab 补全、Enter 确认
- 📝 历史记录：自动保存输入历史，支持快速回溯
- 🎨 丰富图标：根据文件类型显示不同图标
- 📂 递归扫描：自动索引子目录文件

**弹出式文件选择**
- 📋 美观的表格式选择菜单
- ✨ 高亮显示匹配部分
- 🔢 数字快速选择
- ⏭️ 支持跳过选择（按 `s`）
- 🎯 默认选择（按 Enter 使用第一个）

**增强功能**
- Ctrl+Space 手动触发补全菜单
- 鼠标支持（可点击选择）
- 后台线程补全（不阻塞输入）
- 多文件引用时依次显示选择菜单

### 🔧 改进

- 优化文件扫描性能（缓存机制）
- 改进模糊匹配算法（精确匹配 > 前缀匹配 > 包含匹配）
- 增强错误处理和降级机制
- 改进用户提示和交互体验

### 📚 文档

- 新增 [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) - 升级指南
- 新增 [docs/SMART_FILE_REFERENCE.md](docs/SMART_FILE_REFERENCE.md) - 完整功能文档
- 新增 [docs/FILE_REFERENCE_POPUP_GUIDE.md](docs/FILE_REFERENCE_POPUP_GUIDE.md) - 弹出选择指南
- 更新 [README.md](README.md) - 主文档更新

### 🛠️ 工具

- 新增 [install_prompt_toolkit.py](install_prompt_toolkit.py) - 自动安装脚本
- 新增 [demo_smart_file_input.py](demo_smart_file_input.py) - 交互式演示
- 新增 [test_smart_file_input.py](test_smart_file_input.py) - 功能测试
- 新增 [test_popup_selector.py](test_popup_selector.py) - 弹出选择测试

### 📦 依赖

- 新增 `prompt-toolkit>=3.0.0`（可选，提供增强体验）

### 🔄 兼容性

- 向后兼容：未安装 `prompt-toolkit` 时自动降级到传统模式
- 跨平台支持：Windows、macOS、Linux 全平台兼容
- 保留传统文件选择器（输入单独的 `@`）

---

## [1.0.0] - 2025-10-15

### 初始功能

- 🗣️ 自然语言执行命令
- 📁 @ 智能文件引用（基础版）
- 🧠 对话记忆
- 📝 Git 完整工作流
- 🔍 代码审查
- 📊 数据转换工具
- 🔍 环境诊断
- 📋 待办事项管理
- 🔌 MCP 集成
- 🎯 双 LLM 配置

