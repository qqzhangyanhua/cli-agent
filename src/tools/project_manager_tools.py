"""
项目管理工具 - 智能项目启动和打包
支持自动检测项目类型、分析命令、后台执行并处理依赖问题
"""

import json
import os
import re
import subprocess
import signal
import time
import sys
import select
from pathlib import Path
from typing import Dict, List, Optional
from langchain_core.tools import Tool

from src.core.agent_config import WORKING_DIRECTORY


class ProjectDetector:
    """项目类型检测器"""

    @staticmethod
    def detect_project_type(work_dir: str = None) -> Dict:
        """
        检测项目类型

        Args:
            work_dir: 工作目录,默认使用配置的工作目录

        Returns:
            {
                "type": "nodejs" | "python" | "unknown",
                "package_manager": "pnpm" | "npm" | "yarn" | "pip",
                "config_file": "package.json" | "requirements.txt" | ...,
                "scripts": {...},  # 仅 nodejs
                "main_files": [...],  # 仅 python
                "detected_files": [...]  # 检测到的关键文件
            }
        """
        if work_dir is None:
            work_dir = WORKING_DIRECTORY

        work_path = Path(work_dir)
        result = {
            "type": "unknown",
            "package_manager": "",
            "config_file": "",
            "scripts": {},
            "main_files": [],
            "detected_files": []
        }

        # 检测 Node.js 项目
        package_json = work_path / "package.json"
        if package_json.exists():
            result["type"] = "nodejs"
            result["config_file"] = "package.json"
            result["detected_files"].append("package.json")

            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    result["scripts"] = package_data.get("scripts", {})
            except Exception as e:
                print(f"[项目检测] ⚠️  读取 package.json 失败: {e}")

            # 检测包管理器
            if (work_path / "pnpm-lock.yaml").exists():
                result["package_manager"] = "pnpm"
                result["detected_files"].append("pnpm-lock.yaml")
            elif (work_path / "yarn.lock").exists():
                result["package_manager"] = "yarn"
                result["detected_files"].append("yarn.lock")
            elif (work_path / "package-lock.json").exists():
                result["package_manager"] = "npm"
                result["detected_files"].append("package-lock.json")
            else:
                # 默认使用 pnpm
                result["package_manager"] = "pnpm"

            return result

        # 检测 Python 项目
        python_indicators = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "main.py",
            "app.py",
            "manage.py",
            "run.py"
        ]

        python_files_found = []
        main_files = []

        for indicator in python_indicators:
            file_path = work_path / indicator
            if file_path.exists():
                python_files_found.append(indicator)
                if indicator.endswith('.py'):
                    main_files.append(indicator)

        if python_files_found:
            result["type"] = "python"
            result["package_manager"] = "pip"
            result["detected_files"] = python_files_found
            result["main_files"] = main_files

            # 确定配置文件优先级
            if "requirements.txt" in python_files_found:
                result["config_file"] = "requirements.txt"
            elif "pyproject.toml" in python_files_found:
                result["config_file"] = "pyproject.toml"
            elif "setup.py" in python_files_found:
                result["config_file"] = "setup.py"

        return result


class CommandAnalyzer:
    """命令分析器"""

    @staticmethod
    def analyze_start_command(project_info: Dict) -> str:
        """分析启动命令"""
        project_type = project_info.get("type", "unknown")

        if project_type == "nodejs":
            package_manager = project_info.get("package_manager", "pnpm")
            scripts = project_info.get("scripts", {})

            # 启动命令优先级
            for script_name in ["dev", "start", "serve", "preview"]:
                if script_name in scripts:
                    return f"{package_manager} {script_name}"

            # 尝试找包含关键词的脚本
            for name in scripts.keys():
                if any(kw in name.lower() for kw in ["dev", "start", "serve"]):
                    return f"{package_manager} {name}"

            return f"{package_manager} start"

        elif project_type == "python":
            main_files = project_info.get("main_files", [])

            for main_file in ["main.py", "app.py", "manage.py", "run.py"]:
                if main_file in main_files:
                    return f"python {main_file}"

            if main_files:
                return f"python {main_files[0]}"

            return "python main.py"

        return ""

    @staticmethod
    def analyze_build_command(project_info: Dict) -> str:
        """分析打包命令"""
        project_type = project_info.get("type", "unknown")

        if project_type == "nodejs":
            package_manager = project_info.get("package_manager", "pnpm")
            scripts = project_info.get("scripts", {})

            for script_name in ["build", "bundle", "dist", "compile"]:
                if script_name in scripts:
                    return f"{package_manager} {script_name}"

            for name in scripts.keys():
                if any(kw in name.lower() for kw in ["build", "bundle", "dist"]):
                    return f"{package_manager} {name}"

            return f"{package_manager} build"

        elif project_type == "python":
            config_file = project_info.get("config_file", "")

            if config_file == "setup.py":
                return "python setup.py build"
            elif config_file == "pyproject.toml":
                return "python -m build"
            else:
                return "python setup.py build"

        return ""

    @staticmethod
    def analyze_install_command(project_info: Dict) -> str:
        """分析依赖安装命令"""
        project_type = project_info.get("type", "unknown")

        if project_type == "nodejs":
            package_manager = project_info.get("package_manager", "pnpm")
            return f"{package_manager} install"

        elif project_type == "python":
            config_file = project_info.get("config_file", "")

            if config_file == "requirements.txt":
                return "pip install -r requirements.txt"
            elif config_file in ["pyproject.toml", "setup.py"]:
                return "pip install -e ."
            else:
                return "pip install -r requirements.txt"

        return ""


# ============================================
# 进程管理器
# ============================================

class ProcessManager:
    """全局进程管理器 - 跟踪后台运行的开发服务器 (持久化)"""

    def __init__(self):
        # 持久化文件路径
        self.state_file = Path.home() / ".dnm_processes.json"
        self.processes: Dict[int, Dict] = {}
        self._load()

    def _load(self):
        """从文件加载进程信息"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # 转换 key 为 int
                    self.processes = {int(k): v for k, v in data.items()}
                # 清理已死进程
                self._cleanup_dead()
            except Exception as e:
                print(f"[进程管理] 加载状态失败: {e}")
                self.processes = {}

    def _save(self):
        """保存进程信息到文件"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processes, f, indent=2)
        except Exception as e:
            print(f"[进程管理] 保存状态失败: {e}")

    def _cleanup_dead(self):
        """清理已死进程"""
        for pid in list(self.processes.keys()):
            try:
                os.kill(pid, 0)
            except (ProcessLookupError, PermissionError):
                del self.processes[pid]
        self._save()

    def register(self, pid: int, command: str, process_type: str, port: str = "", log_file: str = ""):
        """注册进程"""
        self.processes[pid] = {
            "command": command,
            "type": process_type,
            "port": port,
            "log_file": log_file,  # 保存日志文件路径
            "started_at": time.time()
        }
        self._save()
        print(f"[进程管理] 注册 PID={pid}, 端口={port}, 日志={log_file}")

    def unregister(self, pid: int):
        """注销进程"""
        if pid in self.processes:
            del self.processes[pid]
            self._save()

    def get_running(self) -> Dict[int, Dict]:
        """获取运行中的进程"""
        self._cleanup_dead()
        return self.processes.copy()

    def kill_all(self) -> List[int]:
        """杀死所有已注册的进程"""
        killed = []
        for pid in list(self.processes.keys()):
            try:
                # 杀死整个进程组
                os.killpg(pid, signal.SIGTERM)
                killed.append(pid)
                self.unregister(pid)
            except (ProcessLookupError, PermissionError):
                # 进程可能已经不存在
                self.unregister(pid)
        return killed


process_manager = ProcessManager()


# ============================================
# 智能执行器 - 重构版
# ============================================

class SmartExecutor:
    """
    智能命令执行器

    区分两种执行模式:
    - ONESHOT: install/build - 等待完成
    - DAEMON: dev/start - 后台运行
    """

    SUCCESS_PATTERNS = [
        # Next.js - 必须等待编译完成
        r"✓.*?ready in",
        r"✓.*?compiled.*?in",

        # Vite
        r"ready in.*?ms",
        r"local:.*?http://localhost:\d+",

        # Webpack/CRA
        r"compiled successfully",
        r"webpack.*?compiled",

        # Express/Koa/Flask
        r"listening on",
        r"server.*?started",
        r"running on.*?http",

        # 通用
        r"development server.*?running",
        r"服务.*?启动",
    ]

    ERROR_PATTERNS = [
        r"cannot find module",
        r"modulenotfounderror",
        r"fatal error",
        r"port.*?already.*?in.*?use",
    ]

    INSTALL_NEEDED_PATTERNS = [
        r"cannot find module",
        r"modulenotfounderror",
        r"no module named",
        r"missing.*?dependency",
        r"command not found",           # sh: next: command not found
        r"node_modules.*?missing",      # node_modules missing
        r"did you mean to install",     # pnpm 提示
        r"please.*?install",
        r"run.*?install",
        r"elifecycle.*?command failed", # pnpm/npm 错误
    ]

    def execute_oneshot(self, command: str, work_dir: str, timeout: int = 120) -> Dict:
        """
        执行一次性命令 (install/build)

        等待完成,返回结果
        """
        print(f"[执行] {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            success = result.returncode == 0

            return {
                "success": success,
                "output": result.stdout,
                "error": result.stderr if not success else "",
                "port": ""
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"命令超时 ({timeout}秒)",
                "port": ""
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"执行异常: {str(e)}",
                "port": ""
            }

    def execute_daemon(self, command: str, work_dir: str, timeout: int = 60) -> Dict:
        """
        执行守护进程命令 (dev/start)

        后台运行,监控启动成功,返回端口
        """
        print(f"[后台执行] {command}")

        # 使用固定路径的日志文件 (每个项目一个)
        # 避免日志泄漏,且方便后续查看
        import hashlib
        work_dir_hash = hashlib.md5(work_dir.encode()).hexdigest()[:8]
        log_path = f"/tmp/dnm_{work_dir_hash}.log"

        # 清空旧日志
        with open(log_path, 'w') as f:
            f.write(f"# DNM Log - {work_dir}\n")
            f.write(f"# Command: {command}\n")
            f.write(f"# Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        try:
            # 启动进程,输出重定向到文件
            # 这样进程不会因为stdout被读取而阻塞
            with open(log_path, 'w') as log_f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=work_dir,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    preexec_fn=os.setsid if sys.platform != "win32" else None
                )

            print(f"[进程] PID={process.pid}, 日志={log_path}")

            # 监控日志文件
            output_lines = []
            port = ""
            start_time = time.time()
            is_nextjs = False

            while time.time() - start_time < timeout:
                # 检查进程是否意外退出
                if process.poll() is not None:
                    # 进程退出了,等待日志文件完整写入
                    time.sleep(0.5)

                    # 读取最终日志
                    with open(log_path, 'r') as f:
                        final_output = f.read()

                    return {
                        "success": False,
                        "output": final_output,
                        "error": f"进程意外退出 (code: {process.returncode})",
                        "port": ""
                    }

                # 读取日志文件
                try:
                    with open(log_path, 'r') as f:
                        current_output = f.read()

                    # 只处理新增内容
                    new_lines = current_output[len("\n".join(output_lines)):].split('\n')
                    for line in new_lines:
                        if line.strip():
                            output_lines.append(line.strip())
                            print(f"  {line.strip()}")

                            # 检测 Next.js
                            if "▲ next.js" in line.lower():
                                is_nextjs = True
                                print(f"[检测] Next.js 项目,等待编译完成...")

                            # 提取端口
                            if not port:
                                port = self._extract_port(line)

                    # 检测成功
                    all_output = "\n".join(output_lines).lower()

                    # Next.js 特殊处理
                    if is_nextjs:
                        if re.search(r"✓.*?(ready|compiled)", all_output):
                            print(f"[成功] Next.js 编译完成")

                            # 强制重新提取端口 - 确保是最终端口,不是警告里的
                            port = self._extract_port(all_output) or port
                            print(f"[成功] 最终端口: {port}")

                            process_manager.register(
                                process.pid,
                                command,
                                "dev_server",
                                port,
                                log_path  # 传入日志路径
                            )

                            # 不要关闭进程! 让它继续运行
                            return {
                                "success": True,
                                "output": "\n".join(output_lines),
                                "port": port,
                                "error": "",
                                "process_id": process.pid,
                                "log_file": log_path
                            }
                    else:
                        # 其他框架
                        if self._check_success(all_output):
                            # 强制重新提取端口
                            port = self._extract_port(all_output) or port
                            print(f"[成功] 启动成功, 端口={port}")

                            process_manager.register(
                                process.pid,
                                command,
                                "dev_server",
                                port,
                                log_path  # 传入日志路径
                            )

                            return {
                                "success": True,
                                "output": "\n".join(output_lines),
                                "port": port,
                                "error": "",
                                "process_id": process.pid,
                                "log_file": log_path
                            }

                    # 检测错误
                    if self._check_error(all_output):
                        print(f"[错误] 检测到启动错误, 终止进程...")

                        if process.poll() is None:
                            try:
                                process.terminate()
                                time.sleep(1)

                                if process.poll() is None:
                                    process.kill()
                            except:
                                pass

                        return {
                            "success": False,
                            "output": "\n".join(output_lines),
                            "error": "检测到启动错误, 进程已终止",
                            "port": ""
                        }

                except Exception as read_err:
                    pass  # 文件可能还没创建

                time.sleep(0.5)

            # 超时 - 清理进程!
            print(f"[超时] 启动超时 ({timeout}秒), 终止进程...")

            if process.poll() is None:  # 进程还在运行
                try:
                    process.terminate()  # 先温柔地terminate
                    time.sleep(2)

                    if process.poll() is None:  # 还没死
                        process.kill()  # 强制kill
                        print(f"[超时] 进程已被强制终止")
                except Exception as e:
                    print(f"[超时] 终止进程失败: {e}")

            return {
                "success": False,
                "output": "\n".join(output_lines),
                "error": f"启动超时 ({timeout}秒), 进程已终止",
                "port": ""
            }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"启动异常: {str(e)}",
                "port": ""
            }

    def _extract_port(self, text: str) -> str:
        """提取端口号 - 优先匹配 Local/Server 后的端口"""
        # Next.js/Vite 等: "- Local:   http://localhost:3002"
        priority_patterns = [
            r"local:.*?localhost:(\d+)",
            r"server.*?localhost:(\d+)",
            r"运行.*?localhost:(\d+)",
        ]

        # 优先匹配高优先级模式
        for pattern in priority_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)

        # 兜底: 匹配最后一个 localhost:端口
        matches = re.findall(r"localhost:(\d+)", text.lower())
        if matches:
            return matches[-1]  # 返回最后一个匹配

        # 通用端口模式
        match = re.search(r"port\s+(\d+)", text.lower())
        if match:
            return match.group(1)

        return ""

    def _check_success(self, output: str) -> bool:
        """检查启动成功"""
        for pattern in self.SUCCESS_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def _check_error(self, output: str) -> bool:
        """检查错误"""
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def check_needs_install(self, output: str) -> bool:
        """检查是否需要安装依赖"""
        for pattern in self.INSTALL_NEEDED_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False


# ============================================
# LangChain Tool 封装
# ============================================

def start_project_tool_func(input_str: str) -> str:
    """启动项目工具"""
    try:
        work_dir = os.getcwd()
        if input_str.strip():
            try:
                data = json.loads(input_str)
                work_dir = data.get("work_dir", os.getcwd())
            except json.JSONDecodeError:
                pass

        print(f"\n🚀 [启动项目] 目录: {work_dir}")

        # 1. 检测项目
        project_info = ProjectDetector.detect_project_type(work_dir)
        if project_info["type"] == "unknown":
            return """❌ 未识别项目类型

支持的类型:
  • Node.js (需要 package.json)
  • Python (需要 main.py/app.py 或 requirements.txt)
"""

        print(f"✅ 检测到 {project_info['type'].upper()} 项目")

        # 2. 分析命令
        start_cmd = CommandAnalyzer.analyze_start_command(project_info)
        install_cmd = CommandAnalyzer.analyze_install_command(project_info)

        if not start_cmd:
            return "❌ 无法确定启动命令"

        print(f"🚀 启动命令: {start_cmd}")

        # 3. 执行
        executor = SmartExecutor()
        result = executor.execute_daemon(start_cmd, work_dir, timeout=60)

        # 4. 如果失败且需要安装依赖,自动重试
        if not result["success"] and executor.check_needs_install(result.get("output", "") + result.get("error", "")):
            print("\n" + "="*60)
            print("⚠️  检测到依赖缺失!")
            print(f"🔍 诊断: {result.get('error', '')}")
            print(f"💡 将自动执行: {install_cmd}")
            print("="*60 + "\n")

            install_result = executor.execute_oneshot(install_cmd, work_dir, timeout=120)

            if install_result["success"]:
                print("\n" + "="*60)
                print("✅ 依赖安装成功")
                print("🚀 重新启动项目...")
                print("="*60 + "\n")

                result = executor.execute_daemon(start_cmd, work_dir, timeout=60)
            else:
                return f"""❌ 依赖安装失败

错误: {install_result.get('error', '未知错误')}

输出:
{install_result.get('output', '')[-500:]}
"""

        # 5. 格式化输出
        if result["success"]:
            pid = result.get("process_id", "")
            port = result.get("port", "")

            output_lines = result.get("output", "").split('\n')
            last_lines = output_lines[-3:] if len(output_lines) > 3 else output_lines

            return f"""🎉 项目启动成功!

🌐 访问地址: http://localhost:{port}
🚀 进程ID: {pid}

📋 最后输出:
{chr(10).join(f"   {line}" for line in last_lines if line.strip())}

💡 进程在后台运行
💡 停止服务: dnm "停止项目"
"""
        else:
            return f"""❌ 启动失败

错误: {result.get('error', '未知错误')}

输出:
{result.get('output', '')[-500:]}
"""

    except Exception as e:
        return f"❌ 启动失败: {str(e)}"


def build_project_tool_func(input_str: str) -> str:
    """打包项目工具"""
    try:
        work_dir = os.getcwd()
        if input_str.strip():
            try:
                data = json.loads(input_str)
                work_dir = data.get("work_dir", os.getcwd())
            except json.JSONDecodeError:
                pass

        print(f"\n📦 [打包项目] 目录: {work_dir}")

        # 检测项目
        project_info = ProjectDetector.detect_project_type(work_dir)
        if project_info["type"] == "unknown":
            return "❌ 未识别项目类型"

        # 分析命令
        build_cmd = CommandAnalyzer.analyze_build_command(project_info)
        if not build_cmd:
            return "❌ 无法确定打包命令"

        print(f"📦 打包命令: {build_cmd}")

        # 执行
        executor = SmartExecutor()
        result = executor.execute_oneshot(build_cmd, work_dir, timeout=300)

        if result["success"]:
            # 检测输出目录
            work_path = Path(work_dir)
            found_dirs = []
            for dir_name in ["dist", "build", "out", "public"]:
                if (work_path / dir_name).is_dir():
                    found_dirs.append(dir_name)

            return f"""🎉 打包成功!

📁 输出目录: {', '.join(found_dirs) if found_dirs else '请检查项目目录'}
"""
        else:
            return f"""❌ 打包失败

错误: {result.get('error', '')}
"""

    except Exception as e:
        return f"❌ 打包失败: {str(e)}"


def stop_project_tool_func(input_str: str) -> str:
    """停止项目工具"""
    try:
        pid = None
        port = None

        if input_str.strip():
            try:
                data = json.loads(input_str)
                pid = data.get("pid")
                port = data.get("port")
            except json.JSONDecodeError:
                pass

        print(f"\n🛑 [停止项目]")

        # 如果指定了PID
        if pid:
            try:
                pid_int = int(pid)
                os.killpg(pid_int, signal.SIGTERM)
                time.sleep(1)

                # 检查是否还在运行
                try:
                    os.kill(pid_int, 0)
                    os.killpg(pid_int, signal.SIGKILL)
                except ProcessLookupError:
                    pass

                process_manager.unregister(pid_int)
                return f"✅ 已停止进程 {pid}"

            except (ProcessLookupError, ValueError):
                return f"⚠️  进程 {pid} 不存在"
            except PermissionError:
                return f"❌ 没有权限停止进程 {pid}"

        # 如果指定了端口
        elif port:
            try:
                result = subprocess.run(
                    f"lsof -ti :{port}",
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    stopped = []

                    for pid_str in pids:
                        try:
                            pid_int = int(pid_str)
                            os.killpg(pid_int, signal.SIGTERM)
                            stopped.append(pid_int)
                            process_manager.unregister(pid_int)
                        except:
                            pass

                    return f"""✅ 已停止端口 {port} 的进程
{chr(10).join(f'  • PID {p}' for p in stopped)}
"""
                else:
                    return f"⚠️  端口 {port} 没有被占用"

            except:
                return "❌ 查找进程失败 (需要 lsof)"

        # 停止所有已注册的进程
        else:
            running = process_manager.get_running()
            if running:
                killed = process_manager.kill_all()
                return f"""✅ 已停止所有进程
{chr(10).join(f'  • PID {k}' for k in killed)}
"""
            else:
                return "⚠️  没有运行中的项目进程"

    except Exception as e:
        return f"❌ 停止失败: {str(e)}"


def diagnose_project_tool_func(input_str: str) -> str:
    """诊断项目工具"""
    try:
        pid = None
        port = None

        if input_str.strip():
            try:
                data = json.loads(input_str)
                pid = data.get("pid")
                port = data.get("port")
            except json.JSONDecodeError:
                pass

        result = "🔍 项目诊断报告\n\n"

        # 检查进程
        if pid:
            try:
                os.kill(int(pid), 0)
                result += f"✅ 进程 {pid} 正在运行\n"
            except ProcessLookupError:
                result += f"❌ 进程 {pid} 不存在\n"

        # 检查端口
        if port:
            try:
                check_result = subprocess.run(
                    f"lsof -i :{port}",
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if check_result.returncode == 0:
                    result += f"✅ 端口 {port} 正在被监听\n"
                else:
                    result += f"❌ 端口 {port} 没有被监听\n"
            except:
                result += f"⚠️  无法检查端口 {port}\n"

        # 显示所有运行中的项目
        running = process_manager.get_running()
        if running:
            result += "\n运行中的项目:\n"
            for pid, info in running.items():
                result += f"  • PID {pid}: {info['command']} (端口: {info['port']})\n"

        return result

    except Exception as e:
        return f"❌ 诊断失败: {str(e)}"


# 创建 LangChain Tool 实例
start_project_tool = Tool(
    name="start_project",
    description="""智能启动项目。自动检测项目类型（Node.js/Python），分析启动命令，后台执行并监控输出，自动处理依赖缺失问题。""",
    func=start_project_tool_func
)

build_project_tool = Tool(
    name="build_project",
    description="""智能打包项目。自动检测项目类型，分析打包命令并执行。""",
    func=build_project_tool_func
)

stop_project_tool = Tool(
    name="stop_project",
    description="""停止运行中的项目。可以停止开发服务器、构建进程等。""",
    func=stop_project_tool_func
)

diagnose_project_tool = Tool(
    name="diagnose_project",
    description="""诊断项目运行状态。检查进程、端口、连接等状态，提供详细的诊断报告。""",
    func=diagnose_project_tool_func
)

# 导出工具列表
project_manager_tools = [
    start_project_tool,
    build_project_tool,
    diagnose_project_tool,
    stop_project_tool
]
