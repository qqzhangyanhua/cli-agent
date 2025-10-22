# DNM CLI 安装指南

本文档详细介绍了在不同操作系统上安装 DNM CLI 的方法。

## 目录

- [系统要求](#系统要求)
- [安装方法](#安装方法)
  - [跨平台安装（推荐）](#跨平台安装推荐)
  - [Windows 安装](#windows-安装)
  - [macOS 安装](#macos-安装)
  - [Linux 安装](#linux-安装)
- [配置环境变量](#配置环境变量)
- [验证安装](#验证安装)
- [卸载](#卸载)
- [常见问题](#常见问题)

---

## 系统要求

- **Python**: 3.8 或更高版本
- **pip**: Python 包管理器
- **网络连接**: 用于下载依赖包

### 检查系统要求

```bash
# 检查 Python 版本
python --version   # Windows
python3 --version  # macOS/Linux

# 检查 pip
pip --version      # Windows
pip3 --version     # macOS/Linux
```

---

## 安装方法

### 跨平台安装（推荐）

使用 Python 安装脚本，适用于所有平台：

```bash
# 1. 克隆项目
git clone <repository-url>
cd cli-agent

# 2. 运行安装脚本
python install.py              # Windows
python3 install.py             # macOS/Linux

# 3. 自定义安装目录（可选）
python install.py --dir /your/custom/path

# 4. 仅用户安装，不需要管理员权限
python install.py --user

# 5. 跳过依赖安装（如果已安装）
python install.py --skip-deps
```

**优点：**
- ✅ 跨平台兼容
- ✅ 自动检测系统
- ✅ 智能配置路径
- ✅ 详细的错误提示

---

### Windows 安装

#### 方法1: PowerShell 脚本

1. 打开 PowerShell（建议以管理员身份运行）

2. 如果遇到执行策略限制，运行：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. 运行安装脚本：
   ```powershell
   cd cli-agent
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

4. 或者自定义安装目录：
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1 "C:\your\custom\path"
   ```

#### 方法2: Python 脚本（推荐）

```powershell
cd cli-agent
python install.py
```

#### 安装位置

- **默认位置**: `%LOCALAPPDATA%\Programs\dnm`
  - 通常是: `C:\Users\<用户名>\AppData\Local\Programs\dnm`
- **配置目录**: `%APPDATA%\dnm`
  - 通常是: `C:\Users\<用户名>\AppData\Roaming\dnm`

#### Windows 特殊说明

- 安装脚本会自动创建 `.bat` 批处理启动器
- 如果 PATH 配置成功，重新打开终端即可使用 `dnm` 命令
- 如果遇到 "找不到命令" 错误，需要手动配置 PATH（见下文）

---

### macOS 安装

#### 方法1: Bash 脚本

```bash
cd cli-agent
chmod +x install.sh
./install.sh
```

#### 方法2: Python 脚本

```bash
cd cli-agent
python3 install.py
```

#### 安装位置

- **默认位置**: `~/.local/bin`
- **配置目录**: `~/.config/dnm`

#### macOS 特殊说明

- 需要将 `~/.local/bin` 添加到 PATH
- 使用 Zsh (默认): 编辑 `~/.zshrc`
- 使用 Bash: 编辑 `~/.bashrc`

---

### Linux 安装

#### 方法1: Bash 脚本

```bash
cd cli-agent
chmod +x install.sh
./install.sh
```

#### 方法2: Python 脚本

```bash
cd cli-agent
python3 install.py
```

#### 安装位置

- **默认位置**: `~/.local/bin`
- **配置目录**: `~/.config/dnm`

#### Linux 特殊说明

- 大多数发行版默认包含 `~/.local/bin` 在 PATH 中
- 如果没有，需要手动添加到 shell 配置文件

---

## 配置环境变量

### Windows

#### 图形界面配置

1. 右键 "此电脑" 或 "我的电脑"
2. 点击 "属性"
3. 点击 "高级系统设置"
4. 点击 "环境变量"
5. 在 "用户变量" 中找到 "Path"
6. 点击 "编辑"
7. 点击 "新建"
8. 添加安装目录: `%LOCALAPPDATA%\Programs\dnm`
9. 点击 "确定" 保存

#### PowerShell 配置

```powershell
# 添加到用户 PATH
$installDir = "$env:LOCALAPPDATA\Programs\dnm"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")

# 刷新当前会话
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
```

### macOS / Linux

#### Zsh (macOS 默认)

```bash
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.zshrc
source ~/.zshrc
```

#### Bash

```bash
echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.bashrc
source ~/.bashrc
```

#### Fish Shell

```bash
fish_add_path ~/.local/bin
```

---

## 验证安装

### 检查版本

```bash
dnm --version
```

应该输出:
```
dnm 1.0.0
```

### 测试运行

```bash
# 查看帮助
dnm --help

# 进入交互模式
dnm

# 执行单条命令
dnm "列出当前目录文件"
```

### 检查依赖

```bash
# 检查 Python 模块是否安装
python -c "import langgraph; import langchain_core; import langchain_openai; print('依赖检查通过')"
```

---

## 卸载

### 使用卸载脚本

#### Windows

```powershell
# PowerShell 脚本
powershell -ExecutionPolicy Bypass -File uninstall.ps1

# Python 脚本
python uninstall.py
```

#### macOS / Linux

```bash
# Bash 脚本
./uninstall.sh

# Python 脚本
python3 uninstall.py
```

### 选项

```bash
# 从自定义目录卸载
python uninstall.py --dir /your/custom/path

# 强制卸载，不询问确认
python uninstall.py --force

# 保留配置目录
python uninstall.py --keep-config
```

### 手动卸载

#### Windows

1. 删除安装目录: `%LOCALAPPDATA%\Programs\dnm`
2. 删除配置目录: `%APPDATA%\dnm`
3. 从 PATH 中移除安装目录

#### macOS / Linux

1. 删除安装文件:
   ```bash
   rm ~/.local/bin/dnm
   rm ~/.local/bin/ai-agent
   rm ~/.local/bin/agent_*.py
   rm ~/.local/bin/mcp_*.py
   # ... 其他模块文件
   ```

2. 删除配置目录:
   ```bash
   rm -rf ~/.config/dnm
   ```

3. 从 shell 配置文件中移除 PATH 配置

---

## 常见问题

### Q1: 安装后找不到 `dnm` 命令

**Windows:**
- 确认 PATH 是否配置正确
- 重新打开终端（新 PATH 生效）
- 使用完整路径测试: `%LOCALAPPDATA%\Programs\dnm\dnm.bat --version`

**macOS/Linux:**
- 检查 `~/.local/bin` 是否在 PATH 中
- 运行: `echo $PATH | grep ".local/bin"`
- 重新加载配置: `source ~/.zshrc` 或 `source ~/.bashrc`

### Q2: Python 依赖安装失败

```bash
# 手动安装依赖
pip install --user langgraph langchain-core langchain-openai

# 如果网络问题，使用国内镜像
pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple langgraph langchain-core langchain-openai
```

### Q3: Windows 执行策略限制

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 临时允许执行
powershell -ExecutionPolicy Bypass -File install.ps1

# 永久更改（当前用户）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q4: macOS 权限问题

```bash
# 给脚本添加执行权限
chmod +x install.sh
chmod +x uninstall.sh

# 如果安装目录权限不足
sudo mkdir -p ~/.local/bin
sudo chown -R $USER ~/.local/bin
```

### Q5: 版本升级

```bash
# 1. 卸载旧版本
python uninstall.py --keep-config

# 2. 拉取最新代码
git pull origin main

# 3. 重新安装
python install.py
```

### Q6: 多版本 Python 环境

```bash
# 指定 Python 版本安装
python3.9 install.py
python3.10 install.py

# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
python install.py
```

### Q7: 网络代理问题

```bash
# 设置 pip 代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# Windows PowerShell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
```

---

## 开发者安装

如果你要开发或调试 DNM CLI:

```bash
# 1. 克隆项目
git clone <repository-url>
cd cli-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 直接运行（不安装）
python dnm "你的命令"
python ai-agent "你的命令"

# 5. 开发模式安装（软链接）
pip install -e .
```

---

## 系统特定注意事项

### Windows 10/11

- 推荐使用 Windows Terminal 获得最佳体验
- PowerShell 7+ 支持更好的 Unicode 和 emoji
- 可以在 WSL2 中使用 Linux 安装方法

### macOS Catalina 及更高版本

- 默认使用 Zsh，不是 Bash
- 需要配置 `~/.zshrc` 而不是 `~/.bashrc`
- 可能需要允许在 "安全性与隐私" 中运行

### Ubuntu/Debian

```bash
# 如果缺少 Python
sudo apt update
sudo apt install python3 python3-pip

# 如果缺少 git
sudo apt install git
```

### CentOS/RHEL

```bash
# 如果缺少 Python
sudo yum install python3 python3-pip

# 如果缺少 git
sudo yum install git
```

---

## 获取帮助

如果遇到问题:

1. 查看 [README.md](../README.md) 的常见问题部分
2. 查看 [项目文档](../docs/)
3. 提交 Issue 到 GitHub 仓库
4. 查看安装脚本的详细输出信息

---

**祝你安装顺利！🎉**
