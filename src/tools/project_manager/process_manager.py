"""
进程管理器
跟踪和管理后台运行的开发服务器进程（持久化）
"""

import json
import os
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.core.agent_config import PROCESS_STATE_FILE, PROCESS_HISTORY_FILE


class ProcessManager:
    """全局进程管理器 - 跟踪后台运行的开发服务器 (持久化)"""

    def __init__(self):
        # 持久化文件路径（可配置）
        self.state_file = Path(PROCESS_STATE_FILE)
        self.history_file = Path(PROCESS_HISTORY_FILE)
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

    def _append_history(self, entry: Dict):
        """追加历史记录（失败不影响主流程）"""
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            if not isinstance(history, list):
                history = []
            history.append(entry)
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[进程管理] 保存历史失败: {e}")

    def _read_history(self) -> List[Dict]:
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[进程管理] 读取历史失败: {e}")
        return []

    def get_last_run(self) -> Optional[Dict]:
        """获取最近一次运行记录（优先返回 stop 事件，其次 start 事件）"""
        history = self._read_history()
        for item in reversed(history):
            if item.get("event") in ("stop", "start"):
                return item
        return None

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

        # 写入历史（start 事件）
        self._append_history({
            "event": "start",
            "pid": pid,
            "command": command,
            "type": process_type,
            "port": port,
            "log_file": log_file,
            "started_at": time.time()
        })

    def unregister(self, pid: int):
        """注销进程"""
        if pid in self.processes:
            # 在删除前记录 stop 历史
            info = self.processes.get(pid, {})
            self._append_history({
                "event": "stop",
                "pid": pid,
                "command": info.get("command", ""),
                "type": info.get("type", ""),
                "port": info.get("port", ""),
                "log_file": info.get("log_file", ""),
                "started_at": info.get("started_at"),
                "ended_at": time.time()
            })

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


# 全局单例 - 其他模块通过此变量访问
process_manager = ProcessManager()
