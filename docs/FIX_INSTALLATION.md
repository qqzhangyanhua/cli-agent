# 修复安装问题

## 问题原因

安装脚本缺少新的 `smart_file_input.py` 模块文件。

## 已修复

✅ 已更新 `install.py` - 添加了 `smart_file_input.py`  
✅ 已更新 `install.ps1` - 添加了 `smart_file_input.py` 和 `auto_commit_tools.py`

## 重新安装步骤

### Windows (PowerShell)

```powershell
# 卸载旧版本
python uninstall.py

# 重新安装
python install.py
```

### 或者使用 PowerShell 脚本

```powershell
# 卸载
.\uninstall.ps1

# 重新安装
.\install.ps1
```

### Linux/macOS

```bash
# 卸载
python3 uninstall.py

# 重新安装
python3 install.py
```

## 验证安装

```bash
# 检查模块是否存在
dnm

# 应该正常启动，不再报错 ModuleNotFoundError
```

## 快速修复（如果不想重新安装）

手动复制文件到安装目录：

### Windows

```powershell
# 找到安装目录
$installDir = "$env:LOCALAPPDATA\Programs\dnm"

# 复制新文件
Copy-Item "smart_file_input.py" $installDir
```

### Linux/macOS

```bash
# 复制到安装目录
cp smart_file_input.py ~/.local/bin/
```

## 完成

重新安装后运行：

```bash
dnm
```

应该可以正常使用，并且享受新的 @ 文件引用功能！

