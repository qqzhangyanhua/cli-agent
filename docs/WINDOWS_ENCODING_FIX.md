# Windows 编码兼容性修复

## 问题描述

在 Windows 平台上执行 Git 命令和其他 subprocess 调用时，出现以下编码错误：

```
UnicodeDecodeError: 'gbk' codec can't decode byte 0xab in position 130: illegal multibyte sequence
```

### 原因分析

1. **Windows 默认编码**: Windows 使用 GBK/CP936 作为默认控制台编码
2. **Git 输出编码**: Git 输出通常使用 UTF-8 编码
3. **编码不匹配**: Python `subprocess.run()` 默认使用系统编码解码输出，导致解码失败

## 解决方案

在所有 `subprocess.run()` 和 `subprocess.Popen()` 调用中添加显式编码参数：

```python
# ❌ 问题代码
result = subprocess.run(
    ["git", "status"],
    capture_output=True,
    text=True
)

# ✅ 修复后
result = subprocess.run(
    ["git", "status"],
    capture_output=True,
    text=True,
    encoding='utf-8',      # 显式指定 UTF-8 编码
    errors='replace'        # 遇到无法解码的字符时替换而非抛出异常
)
```

### 参数说明

- `encoding='utf-8'`: 强制使用 UTF-8 解码输出
- `errors='replace'`: 无法解码的字节替换为 `?`，确保程序不会崩溃

## 已修复的文件

### 核心文件
1. ✅ `git_tools.py` - Git 操作工具
   - `check_git_repo()` - 检查 Git 仓库
   - `get_git_status()` - 获取 Git 状态
   - `get_git_diff()` - 获取 Git diff
   - `get_recent_commits()` - 获取提交历史

2. ✅ `agent_utils.py` - 终端命令执行
   - `execute_terminal_command()` - 执行终端命令

3. ✅ `mcp_manager.py` - MCP 服务器管理
   - `call_mcp_server()` - 调用 MCP 服务器

4. ✅ `env_diagnostic_tools.py` - 环境诊断工具
   - `check_python_env()` - 检查 Python 环境
   - `_get_installed_packages()` - 获取已安装包
   - `_check_tool()` - 检查开发工具

### 安装和测试文件
5. ✅ `install.py` - 安装脚本
   - 依赖安装
   - 版本检测

6. ✅ `test_install.py` - 安装测试
   - pip 检测
   - dnm 命令检测

## 测试验证

### 在 Windows 上测试

```powershell
# 1. 测试 Git 功能
dnm "生成commit日志"

# 2. 测试终端命令
dnm "列出当前目录"

# 3. 测试环境诊断
python env_diagnostic_tools.py

# 4. 测试安装
python test_install.py
```

### 预期结果

所有命令应正常执行，不再出现 `UnicodeDecodeError` 错误。

## 最佳实践

### 编写跨平台的 subprocess 调用

```python
import subprocess
import sys
import platform

def safe_run_command(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """
    跨平台安全的命令执行
    
    Args:
        cmd: 命令列表
        **kwargs: subprocess.run 的其他参数
    
    Returns:
        subprocess.CompletedProcess 对象
    """
    # 始终添加编码参数
    default_kwargs = {
        'capture_output': True,
        'text': True,
        'encoding': 'utf-8',
        'errors': 'replace',
    }
    default_kwargs.update(kwargs)
    
    return subprocess.run(cmd, **default_kwargs)


# 使用示例
result = safe_run_command(["git", "status", "--short"])
if result.returncode == 0:
    print(result.stdout)
```

### 处理不同编码的输出

```python
def detect_and_decode(raw_bytes: bytes) -> str:
    """
    智能检测和解码字节串
    
    Args:
        raw_bytes: 原始字节
    
    Returns:
        解码后的字符串
    """
    # 尝试常见编码
    encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']
    
    for encoding in encodings:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # 全都失败，使用替换策略
    return raw_bytes.decode('utf-8', errors='replace')
```

## 相关资源

- [Python subprocess 文档](https://docs.python.org/3/library/subprocess.html)
- [Windows 编码问题](https://docs.python.org/3/library/codecs.html#standard-encodings)
- [Git 编码配置](https://git-scm.com/docs/git-config#Documentation/git-config.txt-i18ncommitEncoding)

## 注意事项

1. **不要使用 `shell=True` with `encoding`**: 在 Windows 上可能导致额外的编码问题
2. **环境变量**: 确保 Git 配置使用 UTF-8 编码
3. **测试**: 在 Windows 和 Mac/Linux 上都要测试
4. **文件路径**: Windows 路径包含反斜杠，需要正确处理

## 未来改进

- [ ] 添加自动编码检测
- [ ] 创建统一的命令执行包装器
- [ ] 添加更详细的错误日志
- [ ] 支持更多编码格式

