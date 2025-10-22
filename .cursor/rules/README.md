# Cursor 规则索引

这个目录包含了 AI Agent CLI 项目的 Cursor 规则文件，帮助 AI 助手更好地理解项目结构和开发规范。

## 📋 规则列表

### 1️⃣ project-overview.mdc
**类型**: 始终应用 (alwaysApply: true)

项目整体概览，包括：
- 项目简介和核心特性
- 项目入口和模块架构
- 工作流程图
- 双 LLM 架构说明

### 2️⃣ python-style.mdc
**类型**: Python 文件专用 (globs: *.py)

Python 代码规范，包括：
- 通用编码规范（PEP 8）
- 文档字符串格式
- 类型注解要求
- 错误处理规范
- 模块化原则
- LLM 调用规范

### 3️⃣ workflow-development.mdc
**描述**: LangGraph 工作流开发指南

工作流开发规范，包括：
- 工作流架构说明
- 状态定义规范
- 节点开发规范（4 种节点类型）
- 条件路由实现
- 最佳实践
- 添加新节点的步骤

### 4️⃣ file-reference-feature.mdc
**描述**: @ 文件引用功能开发指南

@ 文件引用功能详解，包括：
- 核心模块说明
- 工作流程（3 种模式）
- 支持的语法
- 交互式选择器功能
- 文件内容注入机制
- 错误处理
- 扩展建议

### 5️⃣ mcp-integration.mdc
**描述**: MCP (Model Context Protocol) 集成指南

MCP 集成开发，包括：
- 核心文件说明
- MCP 工作流程
- 配置 MCP 服务器
- 可用的 MCP 工具列表
- 工具选择策略
- 添加新 MCP 服务器的步骤
- 性能优化和调试技巧

### 6️⃣ testing.mdc
**类型**: 测试文件专用 (globs: test_*.py,*_test.py)

测试开发规范，包括：
- 测试文件位置和命名
- 测试结构模板
- Mock 和 Fixture 使用
- 测试覆盖目标
- 运行测试命令
- 测试最佳实践

### 7️⃣ documentation.mdc
**类型**: Markdown 文件专用 (globs: *.md)

文档编写规范，包括：
- 文档结构说明
- Markdown 规范
- Emoji 使用指南
- 文档类型（用户/开发/指南）
- 功能文档模板
- 中文文档规范
- 文档更新规范

## 🎯 规则使用说明

### 自动应用的规则
- `project-overview.mdc` - 每次请求都会自动应用，提供项目上下文

### 文件类型规则
根据文件类型自动应用：
- 编辑 Python 文件时 → 应用 `python-style.mdc`
- 编辑测试文件时 → 应用 `testing.mdc`
- 编辑 Markdown 文件时 → 应用 `documentation.mdc`

### 按需查询规则
通过描述触发：
- 开发工作流 → 查询 `workflow-development.mdc`
- 实现 @ 功能 → 查询 `file-reference-feature.mdc`
- 集成 MCP → 查询 `mcp-integration.mdc`

## 💡 如何使用

### 在 Cursor 中触发规则
1. **自动触发**: 打开对应类型的文件即可
2. **手动触发**: 在聊天中提及相关主题
3. **引用文件**: 规则中使用 `[filename](mdc:filename)` 引用项目文件

### 为什么使用规则？
- ✅ 提供项目上下文给 AI
- ✅ 统一代码风格和规范
- ✅ 加速开发流程
- ✅ 减少重复解释
- ✅ 保持一致性

## 🔄 维护规则

### 何时更新规则
- 项目结构变化时
- 新增核心功能时
- 开发规范变更时
- 最佳实践更新时

### 如何更新规则
1. 编辑对应的 `.mdc` 文件
2. 确保 frontmatter 格式正确
3. 使用 `[filename](mdc:filename)` 引用文件
4. 保持中文清晰友好

## 📚 相关资源

- [Cursor Rules 官方文档](https://docs.cursor.com/advanced/rules)
- [项目主文档](mdc:README.md)
- [开发文档目录](mdc:docs/)

---

**最后更新**: 2025-10-22
**规则版本**: 1.0.0

