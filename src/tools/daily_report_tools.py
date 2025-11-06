"""
日报助手工具 - 自动汇总当天活动并生成日报
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from langchain_core.tools import Tool

from src.core.agent_memory import memory
from src.core.agent_llm import llm_code
from src.core.agent_config import (
    DEFAULT_DAILY_REPORT_TEMPLATE,
    DAILY_REPORT_DIR,
    AUTO_SAVE_DAILY_REPORT
)
from langchain_core.messages import HumanMessage


class DailyReportCollector:
    """日报数据收集器"""
    
    def __init__(self, work_dir: str = None):
        """
        初始化日报收集器
        
        Args:
            work_dir: 工作目录，默认为当前目录
        """
        self.work_dir = work_dir or os.getcwd()
        self.today = datetime.now().strftime("%Y-%m-%d")
        
    def collect_git_commits(self) -> List[Dict[str, Any]]:
        """
        收集当天的 Git 提交记录
        
        Returns:
            Git 提交记录列表
        """
        commits = []
        try:
            # 获取当天的提交记录
            cmd = [
                "git", "log", 
                "--since=midnight", 
                "--until=23:59:59",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=format:%H:%M:%S"
            ]
            
            result = subprocess.run(
                cmd, 
                cwd=self.work_dir,
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('|', 3)
                        if len(parts) == 4:
                            commits.append({
                                "hash": parts[0][:8],
                                "author": parts[1],
                                "time": parts[2],
                                "message": parts[3],
                                "full_hash": parts[0]
                            })
            
            # 如果没有当天提交，获取最近3天的提交作为参考
            if not commits:
                cmd_recent = [
                    "git", "log", 
                    "--since=3.days.ago",
                    "--pretty=format:%H|%an|%ad|%s",
                    "--date=format:%Y-%m-%d %H:%M:%S",
                    "-10"  # 最多10条
                ]
                
                result_recent = subprocess.run(
                    cmd_recent,
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result_recent.returncode == 0 and result_recent.stdout.strip():
                    for line in result_recent.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split('|', 3)
                            if len(parts) == 4:
                                commits.append({
                                    "hash": parts[0][:8],
                                    "author": parts[1],
                                    "time": parts[2],
                                    "message": parts[3],
                                    "full_hash": parts[0],
                                    "is_recent": True  # 标记为最近提交
                                })
                                
        except Exception as e:
            print(f"⚠️ 收集 Git 提交时出错: {e}")
            
        return commits
    
    def collect_command_history(self) -> List[Dict[str, Any]]:
        """
        收集当天的命令执行历史
        
        Returns:
            命令执行记录列表
        """
        commands = []
        
        # 从内存中获取命令历史
        if hasattr(memory, 'command_history') and memory.command_history:
            today_str = self.today
            for cmd_record in memory.command_history:
                # 检查是否是今天的命令
                if cmd_record.get('timestamp', '').startswith(today_str):
                    commands.append({
                        "command": cmd_record.get('command', ''),
                        "output": cmd_record.get('output', '')[:100],  # 限制输出长度
                        "success": cmd_record.get('success', True),
                        "time": cmd_record.get('timestamp', '').split(' ')[-1] if ' ' in cmd_record.get('timestamp', '') else ''
                    })
        
        # 尝试从 shell 历史文件中获取更多信息
        try:
            history_files = [
                os.path.expanduser("~/.zsh_history"),
                os.path.expanduser("~/.bash_history"),
                os.path.expanduser("~/.history")
            ]
            
            for history_file in history_files:
                if os.path.exists(history_file):
                    try:
                        with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()[-50:]  # 最近50条
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    # 简单过滤，只保留有意义的命令
                                    if any(keyword in line.lower() for keyword in 
                                          ['git', 'npm', 'python', 'pip', 'cd', 'ls', 'mkdir', 'cp', 'mv']):
                                        commands.append({
                                            "command": line,
                                            "output": "",
                                            "success": True,
                                            "time": "",
                                            "source": "shell_history"
                                        })
                        break  # 找到一个历史文件就够了
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"⚠️ 读取命令历史时出错: {e}")
            
        return commands[-20:]  # 最多返回20条命令
    
    def collect_conversation_history(self) -> List[Dict[str, Any]]:
        """
        收集当天的对话历史
        
        Returns:
            对话记录列表
        """
        conversations = []
        
        if hasattr(memory, 'history') and memory.history:
            today_str = self.today
            for interaction in memory.history:
                # 检查是否是今天的对话
                if interaction.get('timestamp', '').startswith(today_str):
                    conversations.append({
                        "user_input": interaction.get('user', ''),
                        "agent_response": interaction.get('agent', '')[:200],  # 限制长度
                        "intent": interaction.get('intent', 'unknown'),
                        "time": interaction.get('timestamp', '').split(' ')[-1] if ' ' in interaction.get('timestamp', '') else ''
                    })
        
        return conversations
    
    def collect_project_info(self) -> Dict[str, Any]:
        """
        收集项目基本信息
        
        Returns:
            项目信息字典
        """
        project_info = {
            "name": os.path.basename(self.work_dir),
            "path": self.work_dir,
            "git_branch": "unknown",
            "git_status": "unknown",
            "files_changed": 0
        }
        
        try:
            # 获取当前分支
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                project_info["git_branch"] = result.stdout.strip()
            
            # 获取 Git 状态
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                project_info["files_changed"] = len([l for l in lines if l.strip()])
                if project_info["files_changed"] > 0:
                    project_info["git_status"] = f"{project_info['files_changed']} 个文件有变更"
                else:
                    project_info["git_status"] = "工作区干净"
                    
        except Exception as e:
            print(f"⚠️ 收集项目信息时出错: {e}")
            
        return project_info
    
    def collect_all_data(self) -> Dict[str, Any]:
        """
        收集所有日报数据
        
        Returns:
            完整的日报数据字典
        """
        print("📊 正在收集日报数据...")
        
        data = {
            "date": self.today,
            "project": self.collect_project_info(),
            "git_commits": self.collect_git_commits(),
            "commands": self.collect_command_history(),
            "conversations": self.collect_conversation_history(),
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"✅ 数据收集完成:")
        print(f"   📝 Git 提交: {len(data['git_commits'])} 条")
        print(f"   💻 命令执行: {len(data['commands'])} 条")
        print(f"   💬 对话记录: {len(data['conversations'])} 条")
        
        return data


class DailyReportGenerator:
    """日报生成器"""
    
    def __init__(self):
        """初始化日报生成器"""
        self.templates = {
            "standard": self._get_standard_template(),
            "technical": self._get_technical_template(),
            "summary": self._get_summary_template()
        }
    
    def _get_standard_template(self) -> str:
        """获取标准日报模板"""
        return """请基于以下数据生成一份专业的工作日报：

## 📅 日期
{date}

## 📊 项目概况
- 项目名称: {project_name}
- Git 分支: {git_branch}
- 工作状态: {git_status}

## 💻 今日工作内容

### 🔧 代码提交记录
{git_commits_section}

### 💻 命令执行记录
{commands_section}

### 💬 主要交互记录
{conversations_section}

## 📈 工作总结
请基于以上数据，生成一份简洁明了的工作总结，包括：
1. 主要完成的工作
2. 技术要点和难点
3. 明天的计划建议

请用专业、简洁的语言，突出重点工作内容。"""

    def _get_technical_template(self) -> str:
        """获取技术详细模板"""
        return """请基于以下技术数据生成详细的技术日报：

## 🔬 技术日报 - {date}

### 📋 项目状态
- 项目: {project_name} ({project_path})
- 分支: {git_branch}
- 状态: {git_status}

### 💾 代码变更分析
{git_commits_section}

### ⚡ 执行的技术操作
{commands_section}

### 🤖 AI 助手交互
{conversations_section}

### 📊 技术总结
请分析以上数据，生成技术总结：
1. 代码变更的技术影响
2. 执行的关键技术操作
3. 遇到的技术问题和解决方案
4. 技术债务和改进建议"""

    def _get_summary_template(self) -> str:
        """获取简要总结模板"""
        return """基于以下工作数据，生成简要的工作总结：

日期: {date}
项目: {project_name}

Git 提交: {git_commits_count} 条
命令执行: {commands_count} 条
AI 交互: {conversations_count} 次

{git_commits_section}
{commands_section}

请生成一个简洁的工作总结（3-5句话），突出今天的主要工作成果。"""
    
    def _format_git_commits(self, commits: List[Dict]) -> str:
        """格式化 Git 提交记录"""
        if not commits:
            return "📭 今日暂无代码提交"
        
        sections = []
        today_commits = [c for c in commits if not c.get('is_recent', False)]
        recent_commits = [c for c in commits if c.get('is_recent', False)]
        
        if today_commits:
            sections.append("**今日提交:**")
            for commit in today_commits:
                sections.append(f"- `{commit['hash']}` {commit['time']} - {commit['message']}")
        
        if recent_commits and not today_commits:
            sections.append("**最近提交记录（参考）:**")
            for commit in recent_commits[:5]:  # 最多显示5条
                sections.append(f"- `{commit['hash']}` {commit['time']} - {commit['message']}")
        
        return "\n".join(sections) if sections else "📭 暂无提交记录"
    
    def _format_commands(self, commands: List[Dict]) -> str:
        """格式化命令执行记录"""
        if not commands:
            return "📭 今日暂无命令执行记录"
        
        sections = []
        # 按类型分组
        git_commands = [c for c in commands if 'git' in c['command'].lower()]
        npm_commands = [c for c in commands if any(kw in c['command'].lower() for kw in ['npm', 'yarn', 'pnpm'])]
        python_commands = [c for c in commands if any(kw in c['command'].lower() for kw in ['python', 'pip'])]
        other_commands = [c for c in commands if c not in git_commands + npm_commands + python_commands]
        
        if git_commands:
            sections.append("**Git 操作:**")
            for cmd in git_commands[:5]:
                status = "✅" if cmd['success'] else "❌"
                sections.append(f"- {status} `{cmd['command']}`")
        
        if npm_commands:
            sections.append("**包管理操作:**")
            for cmd in npm_commands[:3]:
                status = "✅" if cmd['success'] else "❌"
                sections.append(f"- {status} `{cmd['command']}`")
        
        if python_commands:
            sections.append("**Python 操作:**")
            for cmd in python_commands[:3]:
                status = "✅" if cmd['success'] else "❌"
                sections.append(f"- {status} `{cmd['command']}`")
        
        if other_commands:
            sections.append("**其他操作:**")
            for cmd in other_commands[:5]:
                status = "✅" if cmd['success'] else "❌"
                sections.append(f"- {status} `{cmd['command']}`")
        
        return "\n".join(sections) if sections else "📭 暂无命令记录"
    
    def _format_conversations(self, conversations: List[Dict]) -> str:
        """格式化对话记录"""
        if not conversations:
            return "📭 今日暂无 AI 助手交互记录"
        
        sections = []
        # 按意图分组
        intent_groups = {}
        for conv in conversations:
            intent = conv.get('intent', 'unknown')
            if intent not in intent_groups:
                intent_groups[intent] = []
            intent_groups[intent].append(conv)
        
        intent_names = {
            'question': '💬 问答交互',
            'terminal_command': '💻 命令生成',
            'add_todo': '📝 待办管理',
            'git_commit': '🔧 Git 操作',
            'mcp_tool_call': '🔧 工具调用',
            'unknown': '❓ 其他交互'
        }
        
        for intent, convs in intent_groups.items():
            if len(convs) > 0:
                intent_name = intent_names.get(intent, f'🔧 {intent}')
                sections.append(f"**{intent_name}** ({len(convs)} 次):")
                for conv in convs[:3]:  # 最多显示3条
                    user_input = conv['user_input'][:50] + "..." if len(conv['user_input']) > 50 else conv['user_input']
                    sections.append(f"- {conv.get('time', '')} 用户: {user_input}")
        
        return "\n".join(sections) if sections else "📭 暂无交互记录"
    
    def generate_report(self, data: Dict[str, Any], template_type: str = "standard") -> str:
        """
        生成日报
        
        Args:
            data: 日报数据
            template_type: 模板类型 (standard/technical/summary)
        
        Returns:
            生成的日报内容
        """
        print(f"📝 正在生成日报 (模板: {template_type})...")
        
        template = self.templates.get(template_type, self.templates["standard"])
        
        # 准备模板变量
        project = data.get('project', {})
        template_vars = {
            'date': data.get('date', ''),
            'project_name': project.get('name', '未知项目'),
            'project_path': project.get('path', ''),
            'git_branch': project.get('git_branch', 'unknown'),
            'git_status': project.get('git_status', 'unknown'),
            'git_commits_section': self._format_git_commits(data.get('git_commits', [])),
            'commands_section': self._format_commands(data.get('commands', [])),
            'conversations_section': self._format_conversations(data.get('conversations', [])),
            'git_commits_count': len(data.get('git_commits', [])),
            'commands_count': len(data.get('commands', [])),
            'conversations_count': len(data.get('conversations', []))
        }
        
        # 填充模板
        prompt = template.format(**template_vars)
        
        try:
            # 使用 LLM 生成日报
            result = llm_code.invoke([HumanMessage(content=prompt)])
            report_content = result.content.strip()
            
            print("✅ 日报生成完成")
            return report_content
            
        except Exception as e:
            print(f"❌ 生成日报时出错: {e}")
            # 返回基础格式的日报
            return self._generate_basic_report(data)
    
    def _generate_basic_report(self, data: Dict[str, Any]) -> str:
        """生成基础格式的日报（当 LLM 调用失败时使用）"""
        project = data.get('project', {})
        
        report = f"""# 📅 工作日报 - {data.get('date', '')}

## 📊 项目信息
- **项目名称**: {project.get('name', '未知项目')}
- **Git 分支**: {project.get('git_branch', 'unknown')}
- **工作状态**: {project.get('git_status', 'unknown')}

## 💻 今日工作

### 🔧 代码提交
{self._format_git_commits(data.get('git_commits', []))}

### 💻 命令执行
{self._format_commands(data.get('commands', []))}

### 💬 AI 交互
{self._format_conversations(data.get('conversations', []))}

## 📈 统计信息
- Git 提交: {len(data.get('git_commits', []))} 条
- 命令执行: {len(data.get('commands', []))} 条
- AI 交互: {len(data.get('conversations', []))} 次

---
*报告生成时间: {data.get('collection_time', '')}*
"""
        return report


def generate_daily_report_func(input_str: str) -> str:
    """
    生成日报的工具函数
    
    Args:
        input_str: JSON 格式的参数字符串
    
    Returns:
        生成的日报内容
    """
    try:
        # 解析参数
        if input_str.strip():
            params = json.loads(input_str)
        else:
            params = {}
        
        work_dir = params.get('work_dir', os.getcwd())
        template_type = params.get('template', DEFAULT_DAILY_REPORT_TEMPLATE)
        save_file = params.get('save_file', AUTO_SAVE_DAILY_REPORT)
        
        # 收集数据
        collector = DailyReportCollector(work_dir)
        data = collector.collect_all_data()
        
        # 生成日报
        generator = DailyReportGenerator()
        report = generator.generate_report(data, template_type)
        
        # 保存到文件（可选）
        if save_file:
            today = datetime.now().strftime("%Y-%m-%d")
            filename = f"daily_report_{today}.md"
            
            # 创建日报目录
            report_dir = os.path.join(work_dir, DAILY_REPORT_DIR)
            os.makedirs(report_dir, exist_ok=True)
            
            filepath = os.path.join(report_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"📄 日报已保存到: {filepath}")
            except Exception as e:
                print(f"⚠️ 保存日报文件时出错: {e}")
        
        # 根据是否保存文件返回不同格式
        if save_file:
            return f"""✅ 日报生成完成！

{report}

📊 数据统计:
- Git 提交: {len(data['git_commits'])} 条
- 命令执行: {len(data['commands'])} 条  
- AI 交互: {len(data['conversations'])} 次
"""
        else:
            # UI调用时的简洁格式
            return f"""{report}

📊 数据统计: Git提交 {len(data['git_commits'])} 条 | 命令执行 {len(data['commands'])} 条 | AI交互 {len(data['conversations'])} 次"""
        
    except Exception as e:
        return f"❌ 生成日报时发生错误: {str(e)}"


# 创建 LangChain Tool
generate_daily_report_tool = Tool(
    name="generate_daily_report",
    description="生成日报。汇总当天的 Git 提交、命令执行、AI 交互等活动，自动生成工作日报。支持不同的模板类型。",
    func=generate_daily_report_func
)

# 导出工具列表
daily_report_tools = [generate_daily_report_tool]
