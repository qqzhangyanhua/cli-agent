"""
命令分析器
根据项目类型分析启动、打包、安装命令
"""

from typing import Dict


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
