"""
智能命令执行器
区分一次性命令（install/build）和守护进程（dev/start）
"""

import hashlib
import os
import re
import subprocess
import sys
import time
from typing import Dict

from src.tools.project_manager.process_manager import process_manager


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
