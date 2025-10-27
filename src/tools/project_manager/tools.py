"""
项目管理工具 - LangChain Tool 封装
提供智能项目启动、打包、停止和诊断功能
"""

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from langchain_core.tools import Tool

from src.core.agent_config import WORKING_DIRECTORY, EMPTY_STATE_MESSAGE
from src.tools.project_manager.detector import ProjectDetector
from src.tools.project_manager.analyzer import CommandAnalyzer
from src.tools.project_manager.executor import SmartExecutor
from src.tools.project_manager.process_manager import process_manager


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
                return f"⚠️  {EMPTY_STATE_MESSAGE}"

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
        has_any_output = False  # 是否有任何有效诊断输出（用于空结果兜底）

        # 检查进程
        if pid:
            try:
                os.kill(int(pid), 0)
                result += f"✅ 进程 {pid} 正在运行\n"
                has_any_output = True
            except ProcessLookupError:
                result += f"❌ 进程 {pid} 不存在\n"
                has_any_output = True

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
                has_any_output = True
            except:
                result += f"⚠️  无法检查端口 {port}\n"
                has_any_output = True

        # 显示所有运行中的项目
        running = process_manager.get_running()
        if running:
            result += "\n运行中的项目:\n"
            for pid, info in running.items():
                result += f"  • PID {pid}: {info['command']} (端口: {info['port']})\n"
            has_any_output = True

        # 兜底：如果没有任何有效诊断信息与运行中项目，明确给出提示
        if not has_any_output:
            result += f"{EMPTY_STATE_MESSAGE}\n"
            # 附加最近一次运行信息（如有）
            last = process_manager.get_last_run()
            if last:
                def _fmt(ts):
                    try:
                        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) if ts else ""
                    except Exception:
                        return str(ts)
                result += "\n最近一次运行:\n"
                result += f"  • 命令: {last.get('command', '')}\n"
                if last.get('port'):
                    result += f"  • 端口: {last.get('port')}\n"
                if last.get('log_file'):
                    result += f"  • 日志: {last.get('log_file')}\n"
                if last.get('event') == 'stop':
                    result += f"  • 启动时间: {_fmt(last.get('started_at'))}\n"
                    result += f"  • 结束时间: {_fmt(last.get('ended_at'))}\n"
                else:
                    result += f"  • 启动时间: {_fmt(last.get('started_at'))}\n"
                    result += "  • 状态: 运行记录未正常结束\n"

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
