"""
环境诊断工具模块
检测和诊断开发环境配置
"""

import sys
import os
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any
import json


class EnvironmentDiagnostic:
    """环境诊断器"""
    
    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir).resolve()
    
    def check_python_env(self) -> Dict[str, Any]:
        """检查Python环境"""
        result = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_executable": sys.executable,
            "pip_version": "",
            "virtual_env": "",
            "issues": [],
            "suggestions": []
        }
        
        # 检查pip
        try:
            pip_result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if pip_result.returncode == 0:
                result["pip_version"] = pip_result.stdout.strip()
            else:
                result["issues"].append("pip未正确安装")
        except Exception as e:
            result["issues"].append(f"pip检查失败: {str(e)}")
        
        # 检查虚拟环境
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            result["virtual_env"] = "✅ 已激活"
        else:
            result["virtual_env"] = "⚠️  未激活"
            result["suggestions"].append("建议使用虚拟环境")
        
        return result
    
    def check_dependencies(self) -> Dict[str, Any]:
        """检查项目依赖"""
        result = {
            "requirements_file": "",
            "missing_packages": [],
            "issues": [],
            "suggestions": []
        }
        
        req_path = self.working_dir / "requirements.txt"
        if req_path.exists():
            result["requirements_file"] = str(req_path)
            
            try:
                requirements = self._parse_requirements(req_path)
                installed = self._get_installed_packages()
                
                for pkg_name in requirements.keys():
                    if pkg_name not in installed:
                        result["missing_packages"].append(pkg_name)
                        result["issues"].append(f"缺失包: {pkg_name}")
                
                if result["missing_packages"]:
                    result["suggestions"].append(f"安装缺失包: pip install {' '.join(result['missing_packages'])}")
            
            except Exception as e:
                result["issues"].append(f"解析依赖文件失败: {str(e)}")
        else:
            result["issues"].append("未找到 requirements.txt")
        
        return result
    
    def _parse_requirements(self, req_file: Path) -> Dict[str, str]:
        """解析 requirements.txt"""
        requirements = {}
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-'):
                    continue
                if '==' in line:
                    pkg_name, version = line.split('==')
                    requirements[pkg_name.strip()] = version.strip()
                else:
                    requirements[line.strip()] = ""
        return requirements
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """获取已安装的包"""
        installed = {}
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    installed[pkg['name']] = pkg['version']
        except Exception as e:
            print(f"[包列表] 错误: {e}")
        return installed
    
    def check_dev_tools(self) -> Dict[str, Any]:
        """检查开发工具"""
        result = {
            "tools": {},
            "issues": []
        }
        
        tools = {
            'git': ['git', '--version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'docker': ['docker', '--version'],
        }
        
        for tool_name, command in tools.items():
            tool_info = self._check_tool(command)
            result["tools"][tool_name] = tool_info
            if not tool_info["installed"]:
                result["issues"].append(f"{tool_name} 未安装")
        
        return result
    
    def _check_tool(self, command: List[str]) -> Dict[str, Any]:
        """检查工具是否安装"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return {
                    "installed": True,
                    "version": result.stdout.strip().split('\n')[0]
                }
        except:
            pass
        return {"installed": False, "version": ""}
    
    def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        result = {
            "os": platform.system(),
            "machine": platform.machine(),
            "disk_space": {},
            "issues": []
        }
        
        try:
            disk_usage = shutil.disk_usage(self.working_dir)
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            result["disk_space"] = {
                "free": f"{free_gb:.2f} GB",
                "total": f"{total_gb:.2f} GB",
                "usage_percent": f"{usage_percent:.1f}%"
            }
            
            if free_gb < 5:
                result["issues"].append(f"磁盘空间不足 ({free_gb:.2f} GB)")
        except Exception as e:
            result["issues"].append(f"磁盘检查失败: {str(e)}")
        
        return result
    
    def diagnose(self) -> Dict[str, Any]:
        """执行完整诊断"""
        print("[环境诊断] 开始诊断...")
        
        report = {
            "python_env": self.check_python_env(),
            "dependencies": self.check_dependencies(),
            "dev_tools": self.check_dev_tools(),
            "system": self.check_system_resources()
        }
        
        all_issues = []
        all_suggestions = []
        
        for section, data in report.items():
            all_issues.extend(data.get("issues", []))
            all_suggestions.extend(data.get("suggestions", []))
        
        report["summary"] = {
            "total_issues": len(all_issues),
            "all_issues": all_issues,
            "all_suggestions": all_suggestions
        }
        
        print(f"[环境诊断] 完成 - 发现 {len(all_issues)} 个问题")
        return report


class EnvironmentDiagnosticTools:
    """环境诊断工具集成类"""
    
    def __init__(self, working_dir: str = "."):
        self.diagnostic = EnvironmentDiagnostic(working_dir)
    
    def full_diagnostic(self) -> Dict[str, Any]:
        """执行完整诊断"""
        try:
            report = self.diagnostic.diagnose()
            return {"success": True, "report": report}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def format_report(self, report: Dict[str, Any]) -> str:
        """格式化诊断报告"""
        lines = []
        lines.append("🔍 环境诊断报告")
        lines.append("=" * 80)
        lines.append("")
        
        # Python 环境
        if "python_env" in report:
            py_env = report["python_env"]
            lines.append("✅ Python环境" if not py_env.get("issues") else "⚠️  Python环境")
            lines.append(f"   - Python版本: {py_env.get('python_version')}")
            lines.append(f"   - pip: {py_env.get('pip_version', '未知')[:50]}")
            lines.append(f"   - 虚拟环境: {py_env.get('virtual_env')}")
            lines.append("")
        
        # 项目依赖
        if "dependencies" in report:
            deps = report["dependencies"]
            status = "✅" if not deps.get("issues") else "⚠️ "
            lines.append(f"{status} 项目依赖")
            lines.append(f"   - 依赖文件: {deps.get('requirements_file', '未找到')}")
            if deps.get("missing_packages"):
                lines.append(f"   - 缺失包: {', '.join(deps['missing_packages'][:5])}")
            lines.append("")
        
        # 开发工具
        if "dev_tools" in report:
            tools = report["dev_tools"]
            lines.append("🔧 开发工具")
            for tool_name, tool_info in tools.get("tools", {}).items():
                if tool_info.get("installed"):
                    lines.append(f"   - {tool_name}: {tool_info.get('version')[:40]} ✓")
                else:
                    lines.append(f"   - {tool_name}: 未安装 ✗")
            lines.append("")
        
        # 系统资源
        if "system" in report:
            sys_info = report["system"]
            lines.append("💻 系统资源")
            lines.append(f"   - 操作系统: {sys_info.get('os')}")
            disk = sys_info.get("disk_space", {})
            if disk:
                lines.append(f"   - 磁盘空间: {disk.get('free')} 可用 / {disk.get('total')} ({disk.get('usage_percent')} 已使用)")
            lines.append("")
        
        # 总结
        if "summary" in report:
            summary = report["summary"]
            lines.append("📊 诊断总结")
            lines.append(f"   - 发现问题: {summary.get('total_issues', 0)} 个")
            lines.append("")
            
            if summary.get("all_issues"):
                lines.append("❌ 问题列表:")
                for idx, issue in enumerate(summary["all_issues"][:8], 1):
                    lines.append(f"   {idx}. {issue}")
                lines.append("")
            
            if summary.get("all_suggestions"):
                lines.append("💡 改进建议:")
                for idx, suggestion in enumerate(summary["all_suggestions"][:8], 1):
                    lines.append(f"   {idx}. {suggestion}")
                lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


# 全局实例
env_diagnostic_tools = EnvironmentDiagnosticTools()
