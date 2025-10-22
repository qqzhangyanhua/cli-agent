# @ 文件引用功能 - 快速开始

## 🚀 5 分钟上手

### 第 1 步：启动程序

```bash
dnm
# 或
ai-agent
```

### 第 2 步：输入 @

```
👤 你: @
```

**立即显示文件列表**（无需按 Tab）！

### 第 3 步：选择文件

- 继续输入过滤：`@agent`
- 使用 `↑` `↓` 选择文件
- 按 `Enter` 确认

### 第 4 步：继续对话

```
👤 你: @agent_config.py 这个文件是做什么的？
🤖 助手: 这个文件包含智能体的配置...
```

## ✨ 核心特性

### 自动显示
✅ 输入 `@` 后立即显示文件列表  
✅ 无需按 Tab 或任何额外操作

### 智能搜索
```
@cfg    → agent_config.py
@wkf    → agent_workflow.py
@ui     → agent_ui.py
```

### 多文件引用
```
👤 你: 比较 @old.txt 和 @new.txt
```

## 🎯 常用场景

### 1. 查看文件内容
```
👤 你: @README.md 总结这个项目
```

### 2. 分析代码
```
👤 你: @agent_config.py 有哪些配置项？
```

### 3. 比较文件
```
👤 你: @old 和 @new 有什么区别？
```

### 4. 转换格式
```
👤 你: @data.json 转换为 CSV
```

## ⌨️ 快捷键

| 按键 | 功能 |
|------|------|
| `@` | 显示文件列表 |
| `↑` `↓` | 选择文件 |
| `Enter` | 确认 |
| `Tab` | 补全 |

## 💡 高级技巧

### 模糊搜索
输入缩写快速定位：
- `@cfg` → config 文件
- `@test` → 测试文件

### 路径引用
```
@docs/README.md
@test/test_demo.py
```

## 🔧 可选：安装增强功能

获得更好的视觉效果：

```bash
python install_prompt_toolkit.py
```

## 📚 更多文档

- [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) - 详细升级指南
- [docs/SMART_FILE_REFERENCE.md](docs/SMART_FILE_REFERENCE.md) - 完整功能文档

---

就这么简单！开始体验吧 🎉

