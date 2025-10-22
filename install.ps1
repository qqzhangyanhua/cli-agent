# AI Agent CLI 安装脚本 (Windows PowerShell)
# 使用方法: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 开始安装 DNM CLI..." -ForegroundColor Green
Write-Host ""

# 获取脚本所在目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# 检查Python环境
Write-Host "🐍 检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 错误: 未找到 python，请先安装 Python 3.8+" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未找到 python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查pip
try {
    $pipVersion = pip --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 错误: 未找到 pip，请先安装 pip" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ 错误: 未找到 pip，请先安装 pip" -ForegroundColor Red
    exit 1
}

# 安装Python依赖
Write-Host ""
Write-Host "📦 安装Python依赖..." -ForegroundColor Yellow
$requirementsFile = Join-Path $SCRIPT_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "正在安装依赖包..."
    try {
        python -m pip install -r $requirementsFile --user --quiet
        Write-Host "✅ 依赖安装成功" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  依赖安装可能有问题，但继续安装..." -ForegroundColor Yellow
        Write-Host "💡 请手动运行: python -m pip install --user langgraph langchain-core langchain-openai" -ForegroundColor Cyan
    }
} else {
    Write-Host "⚠️  未找到 requirements.txt，跳过依赖安装" -ForegroundColor Yellow
}

# 默认安装目录 (Windows)
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Programs\dnm"

# 检查是否有自定义安装路径
if ($args.Count -gt 0) {
    $INSTALL_DIR = $args[0]
}

Write-Host ""
Write-Host "📦 安装信息:" -ForegroundColor Cyan
Write-Host "   源目录: $SCRIPT_DIR"
Write-Host "   安装目录: $INSTALL_DIR"
Write-Host ""

# 创建安装目录
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "📁 创建安装目录: $INSTALL_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}

# 复制主程序（dnm 和 ai-agent）
Write-Host "📋 复制程序文件..." -ForegroundColor Yellow
$sourceFiles = @("dnm", "ai-agent")
foreach ($file in $sourceFiles) {
    $sourcePath = Join-Path $SCRIPT_DIR $file
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath $INSTALL_DIR -Force
    }
}

# 创建 Windows 批处理启动器
$dnmBat = Join-Path $INSTALL_DIR "dnm.bat"
$dnmPy = Join-Path $INSTALL_DIR "dnm"
@"
@echo off
python "$dnmPy" %*
"@ | Out-File -FilePath $dnmBat -Encoding ASCII

# 创建配置目录
$CONFIG_DIR = Join-Path $env:USERPROFILE ".config\dnm"
if (-not (Test-Path $CONFIG_DIR)) {
    Write-Host "📁 创建配置目录: $CONFIG_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $CONFIG_DIR -Force | Out-Null
}

# 复制模块文件
Write-Host "📦 复制模块文件..." -ForegroundColor Yellow
$MODULES = @(
    "agent_config.py",
    "agent_memory.py",
    "agent_utils.py",
    "agent_llm.py",
    "agent_nodes.py",
    "agent_workflow.py",
    "agent_ui.py",
    "agent_tool_calling.py",
    "mcp_manager.py",
    "mcp_filesystem.py",
    "mcp_config.json",
    "git_tools.py",
    "git_commit_tools.py",
    "auto_commit_tools.py",
    "code_review_tools.py",
    "data_converter_tools.py",
    "env_diagnostic_tools.py",
    "file_reference_parser.py",
    "interactive_file_selector.py",
    "todo_manager.py",
    "todo_tools.py"
)

foreach ($module in $MODULES) {
    $sourcePath = Join-Path $SCRIPT_DIR $module
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath $INSTALL_DIR -Force
    } else {
        Write-Host "⚠️  警告: 找不到 $module" -ForegroundColor Yellow
    }
}

# 检查PATH
Write-Host ""
Write-Host "🔍 检查 PATH 配置..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -like "*$INSTALL_DIR*") {
    Write-Host "✅ $INSTALL_DIR 已在 PATH 中" -ForegroundColor Green
} else {
    Write-Host "⚠️  $INSTALL_DIR 不在 PATH 中，正在添加..." -ForegroundColor Yellow
    
    try {
        # 添加到用户PATH
        $newPath = $currentPath + ";" + $INSTALL_DIR
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        # 更新当前会话的PATH
        $env:Path = $env:Path + ";" + $INSTALL_DIR
        
        Write-Host "✅ 已添加到 PATH" -ForegroundColor Green
        Write-Host "💡 请重新打开终端以生效" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠️  无法自动添加到 PATH，请手动添加:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   1. 打开 '系统属性' -> '环境变量'" -ForegroundColor Cyan
        Write-Host "   2. 在 '用户变量' 中找到 'Path'" -ForegroundColor Cyan
        Write-Host "   3. 添加: $INSTALL_DIR" -ForegroundColor Cyan
        Write-Host ""
    }
}

Write-Host ""
Write-Host "🧪 测试安装..." -ForegroundColor Yellow
try {
    & $dnmBat --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 安装测试成功！" -ForegroundColor Green
    } else {
        Write-Host "⚠️  安装测试失败，可能需要手动检查依赖" -ForegroundColor Yellow
        Write-Host "请尝试运行: pip install --user langgraph langchain-core langchain-openai" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️  安装测试失败，可能需要手动检查依赖" -ForegroundColor Yellow
    Write-Host "请尝试运行: pip install --user langgraph langchain-core langchain-openai" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✅ DNM 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📖 使用方法:" -ForegroundColor Cyan
Write-Host "   dnm                      # 进入交互模式"
Write-Host "   dnm `"列出所有文件`"      # 执行单条命令"
Write-Host "   dnm --help               # 查看帮助"
Write-Host "   dnm files                # 查看@文件引用功能"
Write-Host ""
Write-Host "🎯 新功能:" -ForegroundColor Cyan
Write-Host "   • 输入 @ 启动交互式文件选择器"
Write-Host "   • 输入 @文件名 快速搜索文件"
Write-Host "   • 支持自然语言文件操作"
Write-Host ""
Write-Host "🎉 享受使用 DNM!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 提示: 如果命令不可用，请重新打开终端" -ForegroundColor Yellow



