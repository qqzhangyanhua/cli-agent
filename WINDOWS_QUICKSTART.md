# Windows 快速开始指南

## 🚀 3 步快速安装

### 第 1 步: 检查 Python

打开 PowerShell，检查 Python 是否安装：

```powershell
python --version
```

✅ 如果显示 `Python 3.8` 或更高版本，继续下一步。  
❌ 如果没有，从 [python.org](https://www.python.org/downloads/) 或 Microsoft Store 安装 Python。

### 第 2 步: 运行安装脚本

```powershell
cd cli-agent
python install.py
```

等待安装完成（约 1-2 分钟）。

### 第 3 步: 验证安装

**重新打开 PowerShell 或 CMD**，然后运行：

```powershell
dnm --version
```

✅ 如果显示 `dnm 1.0.0`，安装成功！  
❌ 如果显示 "找不到命令"，查看下面的 [故障排除](#故障排除)。

---

## 🎮 开始使用

### 进入交互模式

```powershell
dnm
```

然后就可以用自然语言对话了：

```
👤 你: 列出所有Python文件
👤 你: 读取README.md
👤 你: 这是做什么的？
👤 你: 创建一个hello.py打印Hello World然后执行
```

### 执行单条命令

```powershell
dnm "列出所有文件"
dnm "显示git状态"
dnm "搜索包含TODO的文件"
```

### 查看帮助

```powershell
dnm --help
```

---

## 🔧 故障排除

### 问题 1: 找不到 `python` 命令

**解决方法：**

1. 从 [python.org](https://www.python.org/downloads/) 下载并安装 Python
2. 安装时勾选 **"Add Python to PATH"**
3. 重新打开 PowerShell

或者从 Microsoft Store 安装：

```powershell
# 打开 Microsoft Store
start ms-windows-store://search/?query=python
```

### 问题 2: 找不到 `dnm` 命令

**原因:** PATH 环境变量未生效

**解决方法 A - 重新打开终端（最简单）:**

关闭当前 PowerShell，重新打开，再试一次：

```powershell
dnm --version
```

**解决方法 B - 使用完整路径:**

```powershell
# 找到安装位置
echo $env:LOCALAPPDATA\Programs\dnm\dnm.bat

# 使用完整路径运行
& "$env:LOCALAPPDATA\Programs\dnm\dnm.bat" --version
```

**解决方法 C - 手动配置 PATH:**

1. 右键 "此电脑" → "属性" → "高级系统设置"
2. 点击 "环境变量"
3. 在 "用户变量" 中找到 "Path"
4. 点击 "编辑" → "新建"
5. 添加: `%LOCALAPPDATA%\Programs\dnm`
6. 点击 "确定" 保存
7. **重新打开终端**

### 问题 3: PowerShell 执行策略错误

**错误信息:**
```
无法加载文件，因为在此系统上禁止运行脚本
```

**解决方法:**

```powershell
# 使用 Python 脚本代替（推荐）
python install.py

# 或者临时允许执行
powershell -ExecutionPolicy Bypass -File install.ps1
```

### 问题 4: 依赖安装失败

**解决方法:**

```powershell
# 手动安装依赖
pip install --user langgraph langchain-core langchain-openai

# 如果网络慢，使用国内镜像
pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple langgraph langchain-core langchain-openai
```

### 问题 5: 中文显示乱码

**解决方法:**

```powershell
# 设置控制台编码为 UTF-8
chcp 65001
```

**推荐:** 使用 **Windows Terminal** 代替 CMD/PowerShell，支持更好。

下载方式：
- 打开 Microsoft Store
- 搜索 "Windows Terminal"
- 安装

---

## 📚 更多功能

### @ 文件引用

```powershell
dnm
# 然后输入: @
# 会启动交互式文件选择器
```

### Git 智能工具

```powershell
dnm "生成commit消息"
dnm "对当前代码进行code review"
```

### 数据转换

```powershell
dnm "@data.json 转换为CSV"
dnm "@config.yaml 验证格式"
```

### 待办事项管理

```powershell
dnm "今天18点给陈龙打电话"
dnm "明天上午10点开会"
dnm "今天有什么要做的"
```

---

## 🗑️ 卸载

如果需要卸载：

```powershell
python uninstall.py
```

---

## 🆘 获取更多帮助

- [完整安装指南](docs/INSTALLATION_GUIDE.md)
- [Windows 详细文档](docs/WINDOWS_INSTALLATION.md)
- [项目 README](README.md)

---

## 💡 小技巧

1. **使用 Windows Terminal** 获得更好的体验
2. **配置好 OpenAI API Key** 才能使用（见项目文档）
3. 在交互模式下输入 `help` 查看所有功能
4. 使用 `history` 查看对话历史
5. 使用 `clear` 清空对话历史

---

**祝你使用愉快！🎉**



