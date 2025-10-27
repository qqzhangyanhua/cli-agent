"""
项目类型检测器
自动检测 Node.js 和 Python 项目
"""

import json
from pathlib import Path
from typing import Dict

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
