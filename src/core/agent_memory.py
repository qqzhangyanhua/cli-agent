"""
对话记忆管理模块
"""

from typing import List, Dict
from datetime import datetime
from src.core.agent_config import MAX_CONVERSATION_HISTORY, MAX_COMMAND_HISTORY


class ConversationMemory:
    """对话记忆管理"""
    
    def __init__(self, max_history: int = MAX_CONVERSATION_HISTORY):
        self.history: List[Dict] = []
        self.max_history = max_history
        self.command_history: List[Dict] = []
    
    def add_interaction(self, user_input: str, agent_response: str, intent: str = "unknown"):
        """添加一次对话交互"""
        interaction = {
            "user": user_input,
            "agent": agent_response,
            "intent": intent,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.append(interaction)
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def add_command(self, command: str, output: str, success: bool = True):
        """添加命令执行记录"""
        cmd_record = {
            "command": command,
            "output": output[:200],
            "success": success,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.command_history.append(cmd_record)
        
        if len(self.command_history) > MAX_COMMAND_HISTORY:
            self.command_history.pop(0)
    
    def get_recent_conversations(self, n: int = 3) -> List[Dict]:
        """获取最近n次对话"""
        return self.history[-n:] if self.history else []
    
    def get_recent_commands(self, n: int = 5) -> str:
        """获取最近n条命令的字符串表示"""
        if not self.command_history:
            return "暂无命令历史"
        
        recent = self.command_history[-n:]
        result = "最近执行的命令:\n"
        for cmd in recent:
            status = "✅" if cmd["success"] else "❌"
            result += f"{status} {cmd['command']}\n"
        return result
    
    def get_context_string(self) -> str:
        """获取上下文字符串"""
        if not self.history:
            return "暂无对话历史"
        
        recent = self.get_recent_conversations(3)
        context = "最近的对话:\n"
        for interaction in recent:
            context += f"用户: {interaction['user']}\n"
            context += f"助手: {interaction['agent'][:100]}...\n"
        return context
    
    def clear(self):
        """清空所有记忆"""
        self.history.clear()
        self.command_history.clear()


# 全局记忆实例
memory = ConversationMemory()
