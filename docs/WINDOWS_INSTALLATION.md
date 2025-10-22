# DNM CLI - Windows 安装指南

## 🚀 快速开始

### 最简单的安装方法（推荐）

```powershell
# 1. 打开 PowerShell
# 2. 进入项目目录
cd cli-agent

# 3. 运行 Python 安装脚本
python install.py
```

安装完成后，重新打开终端，输入 `dnm --version` 验证。

---

## 📋 安装选项

### 选项1: Python 安装脚本（推荐）✅

**优点:**
- ✅ 最简单、最可靠
- ✅ 自动检测环境
- ✅ 跨平台兼容
- ✅ 详细的错误提示

**步骤:**

```powershell
# 基本安装
python install.py

# 自定义安装目录
python install.py --dir "C:\your\custom\path"

# 跳过依赖安装（如果已安装）
python install.py --skip-deps
```

### 选项2: PowerShell 脚本

**步骤:**

```powershell
# 如果遇到执行策略限制，先运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行安装脚本
powershell -ExecutionPolicy Bypass -File install.ps1

# 自定义安装目录
powershell -ExecutionPolicy Bypass -File install.ps1 "C:\your\custom\path"
```

---

## 📍 安装位置

### 默认安装路径

- **程序目录**: `%LOCALAPPDATA%\Programs\dnm`
  - 实际路径: `C:\Users\<你的用户名>\AppData\Local\Programs\dnm`
  
- **配置目录**: `%APPDATA%\dnm`
  - 实际路径: `C:\Users\<你的用户名>\AppData\Roaming\dnm`

### 查看安装位置

```powershell
# 查看程序位置
where dnm

# 查看配置目录
echo %APPDATA%\dnm
```

---

## 🔧 配置 PATH

### 自动配置（推荐）

安装脚本会尝试自动配置 PATH。如果成功，重新打开终端即可使用 `dnm` 命令。

### 手动配置 PATH

如果自动配置失败，按以下步骤手动配置：

#### 图形界面方法

1. 右键 **"此电脑"** 或 **"我的电脑"**
2. 点击 **"属性"**
3. 点击 **"高级系统设置"**
4. 点击 **"环境变量"**
5. 在 **"用户变量"** 中找到 **"Path"**
6. 点击 **"编辑"**
7. 点击 **"新建"**
8. 添加: `%LOCALAPPDATA%\Programs\dnm`
9. 点击 **"确定"** 保存所有对话框

#### PowerShell 方法

```powershell
# 添加到用户 PATH
$installDir = "$env:LOCALAPPDATA\Programs\dnm"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")

# 刷新当前会话的 PATH
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
```

#### 验证 PATH 配置

```powershell
# 检查 PATH 是否包含安装目录
echo $env:Path | Select-String "dnm"

# 测试命令
dnm --version
```

---

## ✅ 验证安装

### 检查版本

```powershell
dnm --version
```

应该输出: `dnm 1.0.0`

### 测试运行

```powershell
# 查看帮助
dnm --help

# 进入交互模式
dnm

# 执行单条命令
dnm "列出当前目录文件"
```

### 检查依赖

```powershell
# 检查 Python 模块
python -c "import langgraph; import langchain_core; import langchain_openai; print('依赖检查通过')"
```

---

## 🗑️ 卸载

### 使用卸载脚本

```powershell
# PowerShell 脚本
powershell -ExecutionPolicy Bypass -File uninstall.ps1

# Python 脚本
python uninstall.py
```

### 手动卸载

1. 删除安装目录:
   ```powershell
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\dnm"
   ```

2. 删除配置目录（可选）:
   ```powershell
   Remove-Item -Recurse -Force "$env:APPDATA\dnm"
   ```

3. 从 PATH 中移除安装目录（参考上面的 PATH 配置方法）

---

## 🐛 常见问题

### Q1: 找不到 `python` 命令

**解决方法:**

1. **检查 Python 是否安装:**
   - 在 Microsoft Store 搜索 "Python" 并安装
   - 或从 [python.org](https://www.python.org/downloads/) 下载

2. **检查 Python 是否在 PATH 中:**
   ```powershell
   python --version
   ```

3. **使用完整路径:**
   ```powershell
   C:\Users\<用户名>\AppData\Local\Programs\Python\Python3X\python.exe install.py
   ```

### Q2: 找不到 `dnm` 命令

**可能原因和解决方法:**

1. **PATH 未配置或未生效**
   - 解决: 重新打开终端
   - 或手动配置 PATH（见上文）

2. **使用完整路径测试:**
   ```powershell
   & "$env:LOCALAPPDATA\Programs\dnm\dnm.bat" --version
   ```

3. **检查文件是否存在:**
   ```powershell
   dir "$env:LOCALAPPDATA\Programs\dnm"
   ```

### Q3: PowerShell 执行策略限制

**错误信息:**
```
无法加载文件 xxx.ps1，因为在此系统上禁止运行脚本
```

**解决方法:**

```powershell
# 方法1: 临时绕过（推荐）
powershell -ExecutionPolicy Bypass -File install.ps1

# 方法2: 更改当前用户策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法3: 查看当前策略
Get-ExecutionPolicy -List
```

### Q4: 依赖安装失败

**错误信息:**
```
ERROR: Could not install packages due to an OSError
```

**解决方法:**

```powershell
# 手动安装依赖
pip install --user langgraph langchain-core langchain-openai

# 使用国内镜像加速
pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple langgraph langchain-core langchain-openai

# 升级 pip
python -m pip install --upgrade pip
```

### Q5: 权限问题

**错误信息:**
```
Access is denied
```

**解决方法:**

1. **以管理员身份运行 PowerShell:**
   - 右键 PowerShell 图标
   - 选择 "以管理员身份运行"

2. **使用用户安装:**
   ```powershell
   python install.py --user
   ```

### Q6: 中文乱码问题

**解决方法:**

```powershell
# 设置控制台编码为 UTF-8
chcp 65001

# 或在 PowerShell 配置文件中添加
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

**推荐:** 使用 **Windows Terminal** 获得更好的 Unicode 支持。

### Q7: 网络代理问题

**解决方法:**

```powershell
# 设置代理
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"

# 安装依赖
pip install --user --proxy http://proxy.example.com:8080 langgraph langchain-core langchain-openai
```

---

## 💡 推荐工具

### Windows Terminal

- **下载:** Microsoft Store 搜索 "Windows Terminal"
- **优点:** 更好的 Unicode 和 emoji 支持，更美观

### PowerShell 7+

- **下载:** [GitHub Releases](https://github.com/PowerShell/PowerShell/releases)
- **优点:** 更现代的 PowerShell，跨平台

### Visual Studio Code

- **下载:** [code.visualstudio.com](https://code.visualstudio.com/)
- **优点:** 集成终端，更好的开发体验

---

## 🔄 升级

```powershell
# 1. 卸载旧版本（保留配置）
python uninstall.py --keep-config

# 2. 拉取最新代码
git pull origin main

# 3. 重新安装
python install.py
```

---

## 📚 相关文档

- [完整安装指南](INSTALLATION_GUIDE.md) - 所有平台的详细说明
- [README.md](../README.md) - 项目主文档
- [快速开始](../README.md#快速安装) - 快速入门

---

## 🆘 获取帮助

如果还有问题:

1. 查看 [完整安装指南](INSTALLATION_GUIDE.md)
2. 查看项目 [常见问题](../README.md#常见问题)
3. 提交 Issue 到 GitHub 仓库

---

**祝你安装顺利！🎉**



