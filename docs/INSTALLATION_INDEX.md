# DNM CLI 安装文档索引

本文档提供所有安装相关文档的快速导航。

## 📚 文档导航

### 🚀 快速开始

- **[Windows 快速开始](../WINDOWS_QUICKSTART.md)** ⭐  
  Windows 用户的 3 步快速安装指南，最简单的入门方式。

- **[主 README](../README.md#快速安装)**  
  项目主文档的安装部分，适合所有平台。

### 📖 完整指南

- **[完整安装指南](INSTALLATION_GUIDE.md)** 📘  
  涵盖所有平台的详细安装说明，包括系统要求、配置方法、常见问题等。

- **[Windows 安装指南](WINDOWS_INSTALLATION.md)** 💻  
  Windows 平台的详细安装文档，包含故障排除和推荐工具。

### 🛠️ 安装脚本

项目提供了多种安装脚本，选择最适合你的：

#### Python 脚本（推荐 ⭐）

- **[install.py](../install.py)** - 跨平台安装脚本  
  适用于 Windows、macOS、Linux
  
  ```bash
  python install.py              # 默认安装
  python install.py --help       # 查看选项
  ```

- **[uninstall.py](../uninstall.py)** - 跨平台卸载脚本
  
  ```bash
  python uninstall.py            # 卸载
  python uninstall.py --help     # 查看选项
  ```

- **[test_install.py](../test_install.py)** - 安装测试脚本
  
  ```bash
  python test_install.py         # 测试安装
  ```

#### Shell 脚本（Unix）

- **[install.sh](../install.sh)** - macOS/Linux 安装脚本
  
  ```bash
  ./install.sh
  ```

- **[uninstall.sh](../uninstall.sh)** - macOS/Linux 卸载脚本
  
  ```bash
  ./uninstall.sh
  ```

#### PowerShell 脚本（Windows）

- **[install.ps1](../install.ps1)** - Windows PowerShell 安装脚本
  
  ```powershell
  powershell -ExecutionPolicy Bypass -File install.ps1
  ```

- **[uninstall.ps1](../uninstall.ps1)** - Windows PowerShell 卸载脚本
  
  ```powershell
  powershell -ExecutionPolicy Bypass -File uninstall.ps1
  ```

---

## 🎯 选择合适的文档

### 我该看哪个文档？

根据你的情况选择：

| 场景 | 推荐文档 | 说明 |
|------|---------|------|
| **Windows 用户，快速上手** | [Windows 快速开始](../WINDOWS_QUICKSTART.md) | 3 步完成安装 |
| **Windows 用户，遇到问题** | [Windows 安装指南](WINDOWS_INSTALLATION.md) | 详细的故障排除 |
| **macOS/Linux 用户** | [完整安装指南](INSTALLATION_GUIDE.md) | 全平台指南 |
| **需要自定义安装** | [完整安装指南](INSTALLATION_GUIDE.md) | 包含高级选项 |
| **开发者** | [完整安装指南](INSTALLATION_GUIDE.md) | 包含开发环境设置 |
| **安装后测试** | [test_install.py](../test_install.py) | 验证安装 |

---

## 📋 安装流程图

```
开始
 ↓
检查 Python 是否安装 (3.8+)
 ↓
选择安装方法
 ├─ Python 脚本 (推荐) ────────┐
 ├─ PowerShell 脚本 (Windows)──┤
 └─ Bash 脚本 (macOS/Linux)────┤
                               ↓
                          运行安装脚本
                               ↓
                          安装依赖包
                               ↓
                          复制文件
                               ↓
                          配置 PATH
                               ↓
                          测试安装
                               ↓
                     ┌─────────┴─────────┐
                     ↓                   ↓
                   成功 ✅             失败 ❌
                     ↓                   ↓
                 开始使用          查看故障排除
```

---

## 🔍 按平台查看

### Windows

1. **快速开始**: [WINDOWS_QUICKSTART.md](../WINDOWS_QUICKSTART.md)
2. **详细指南**: [WINDOWS_INSTALLATION.md](WINDOWS_INSTALLATION.md)
3. **推荐脚本**: [install.py](../install.py) 或 [install.ps1](../install.ps1)
4. **测试工具**: [test_install.py](../test_install.py)

### macOS

1. **完整指南**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. **推荐脚本**: [install.py](../install.py) 或 [install.sh](../install.sh)
3. **测试工具**: [test_install.py](../test_install.py)

### Linux

1. **完整指南**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. **推荐脚本**: [install.py](../install.py) 或 [install.sh](../install.sh)
3. **测试工具**: [test_install.py](../test_install.py)

---

## ✅ 安装后检查清单

安装完成后，按以下清单验证：

- [ ] 运行 `dnm --version` 显示版本号
- [ ] 运行 `dnm --help` 显示帮助信息
- [ ] 运行 `python test_install.py` 所有测试通过
- [ ] 进入交互模式: `dnm`
- [ ] 执行测试命令: `dnm "列出所有文件"`
- [ ] 配置 OpenAI API Key（见主文档）

---

## 🆘 故障排除

### 常见问题快速链接

1. **找不到命令**
   - [Windows 解决方案](WINDOWS_INSTALLATION.md#q2-找不到-dnm-命令)
   - [Unix 解决方案](INSTALLATION_GUIDE.md#q1-安装后找不到-dnm-命令)

2. **依赖安装失败**
   - [解决方案](INSTALLATION_GUIDE.md#q2-python-依赖安装失败)

3. **权限问题**
   - [Windows 权限](WINDOWS_INSTALLATION.md#q5-权限问题)
   - [macOS 权限](INSTALLATION_GUIDE.md#q4-macos-权限问题)

4. **PATH 配置**
   - [Windows PATH](WINDOWS_INSTALLATION.md#手动配置-path)
   - [Unix PATH](INSTALLATION_GUIDE.md#配置环境变量)

### 获取帮助

如果文档无法解决你的问题：

1. 运行 `python test_install.py` 查看具体问题
2. 查看 [完整故障排除列表](INSTALLATION_GUIDE.md#常见问题)
3. 提交 Issue 到 GitHub 仓库

---

## 📝 卸载指南

需要卸载时：

### 使用脚本卸载（推荐）

```bash
# Python 脚本（所有平台）
python uninstall.py

# PowerShell 脚本（Windows）
powershell -ExecutionPolicy Bypass -File uninstall.ps1

# Bash 脚本（macOS/Linux）
./uninstall.sh
```

### 手动卸载

参考：
- [Windows 手动卸载](WINDOWS_INSTALLATION.md#手动卸载)
- [Unix 手动卸载](INSTALLATION_GUIDE.md#手动卸载)

---

## 🔄 版本升级

升级到新版本：

```bash
# 1. 卸载旧版本（保留配置）
python uninstall.py --keep-config

# 2. 拉取最新代码
git pull origin main

# 3. 重新安装
python install.py

# 4. 测试
python test_install.py
```

---

## 💡 推荐阅读顺序

### 新用户

1. [Windows 快速开始](../WINDOWS_QUICKSTART.md) 或 [主 README](../README.md)
2. 运行 `python test_install.py` 测试
3. 如果遇到问题，查看对应平台的详细指南

### 高级用户

1. [完整安装指南](INSTALLATION_GUIDE.md)
2. 自定义安装选项
3. [开发者安装部分](INSTALLATION_GUIDE.md#开发者安装)

---

## 📊 文档对比

| 特性 | 快速开始 | Windows 指南 | 完整指南 |
|-----|---------|-------------|----------|
| 适合人群 | Windows 新手 | Windows 用户 | 所有用户 |
| 页面长度 | 短 | 中 | 长 |
| 细节程度 | 基础 | 详细 | 完整 |
| 故障排除 | 简单 | 详细 | 完整 |
| 平台覆盖 | Windows | Windows | 全平台 |
| 推荐度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🔗 相关资源

- [项目主文档](../README.md)
- [使用示例](../README.md#使用示例)
- [功能文档](../README.md#核心特性)
- [开发文档](../docs/)

### 平台特定问题

- **[Windows 编码兼容性修复](WINDOWS_ENCODING_FIX.md)** 🔧  
  修复 Windows 平台的 UTF-8 编码问题，解决 `UnicodeDecodeError` 错误。
  
  如果在 Windows 上遇到编码错误，请查看此文档。

---

**最后更新**: 2025-10-22  
**版本**: 1.0.0

有任何疑问或建议，欢迎提交 Issue！

