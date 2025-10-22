# AI Agent CLI 卸载脚本 (Windows PowerShell)
# 使用方法: powershell -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = "Stop"

Write-Host "🗑️  开始卸载 DNM CLI..." -ForegroundColor Yellow
Write-Host ""

# 默认安装目录
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Programs\dnm"

# 检查是否有自定义安装路径
if ($args.Count -gt 0) {
    $INSTALL_DIR = $args[0]
}

Write-Host "📦 卸载目录: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host ""

# 检查目录是否存在
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "⚠️  安装目录不存在: $INSTALL_DIR" -ForegroundColor Yellow
    Write-Host "可能已经卸载或从未安装" -ForegroundColor Yellow
    exit 0
}

# 删除主程序
$mainFiles = @("dnm", "dnm.bat", "ai-agent", "ai-agent.bat")
foreach ($file in $mainFiles) {
    $filePath = Join-Path $INSTALL_DIR $file
    if (Test-Path $filePath) {
        Write-Host "🗑️  删除: $filePath" -ForegroundColor Yellow
        Remove-Item $filePath -Force
    }
}

# 删除模块文件
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
    "code_review_tools.py",
    "data_converter_tools.py",
    "env_diagnostic_tools.py",
    "file_reference_parser.py",
    "interactive_file_selector.py",
    "todo_manager.py",
    "todo_tools.py"
)

foreach ($module in $MODULES) {
    $filePath = Join-Path $INSTALL_DIR $module
    if (Test-Path $filePath) {
        Write-Host "🗑️  删除: $filePath" -ForegroundColor Yellow
        Remove-Item $filePath -Force
    }
}

# 删除安装目录（如果为空）
try {
    $items = Get-ChildItem $INSTALL_DIR
    if ($items.Count -eq 0) {
        Write-Host "🗑️  删除空安装目录: $INSTALL_DIR" -ForegroundColor Yellow
        Remove-Item $INSTALL_DIR -Force
    } else {
        Write-Host "⚠️  安装目录不为空，保留: $INSTALL_DIR" -ForegroundColor Yellow
    }
} catch {
    # 目录不存在或无法访问
}

# 可选：删除配置目录
$CONFIG_DIR = Join-Path $env:USERPROFILE ".config\dnm"
if (Test-Path $CONFIG_DIR) {
    Write-Host ""
    $response = Read-Host "是否删除配置目录 $CONFIG_DIR ? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "🗑️  删除配置目录: $CONFIG_DIR" -ForegroundColor Yellow
        Remove-Item $CONFIG_DIR -Recurse -Force
    }
}

Write-Host ""
Write-Host "✅ 卸载完成！" -ForegroundColor Green
Write-Host ""
Write-Host "💡 提示: 如果之前手动添加了 PATH，请记得删除:" -ForegroundColor Cyan
Write-Host "   $INSTALL_DIR" -ForegroundColor Yellow


