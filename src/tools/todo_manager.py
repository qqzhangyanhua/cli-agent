"""
待办事项管理模块
支持按日期存储和查询待办事项
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import uuid


class TodoManager:
    """待办事项管理器"""
    
    def __init__(self, todos_dir: Optional[str] = None):
        """
        初始化待办事项管理器
        
        Args:
            todos_dir: 待办事项存储目录，默认为脚本所在目录下的 todos 文件夹
        """
        if todos_dir is None:
            # 获取当前脚本所在的目录（安装目录）
            script_dir = Path(__file__).parent.absolute()
            todos_dir = script_dir / "todos"
        
        self.todos_dir = Path(todos_dir)
        self.todos_dir.mkdir(exist_ok=True)
    
    def _get_todo_file(self, date: str) -> Path:
        """
        获取指定日期的待办文件路径
        
        Args:
            date: 日期字符串，格式：YYYY-MM-DD
        
        Returns:
            文件路径
        """
        return self.todos_dir / f"{date}.json"
    
    def _load_todos(self, date: str) -> Dict:
        """
        加载指定日期的待办事项
        
        Args:
            date: 日期字符串
        
        Returns:
            待办数据字典
        """
        file_path = self._get_todo_file(date)
        
        if not file_path.exists():
            return {
                "date": date,
                "todos": []
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取待办文件失败: {e}")
            return {
                "date": date,
                "todos": []
            }
    
    def _save_todos(self, date: str, data: Dict) -> bool:
        """
        保存待办事项到文件
        
        Args:
            date: 日期字符串
            data: 待办数据
        
        Returns:
            是否成功
        """
        file_path = self._get_todo_file(date)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 保存待办文件失败: {e}")
            return False
    
    def add_todo(self, date: str, time: str, content: str, **kwargs) -> Dict:
        """
        添加待办事项
        
        Args:
            date: 日期，格式：YYYY-MM-DD
            time: 时间，格式：HH:MM
            content: 待办内容
            **kwargs: 其他自定义字段
        
        Returns:
            添加的待办事项
        """
        data = self._load_todos(date)
        
        todo_item = {
            "id": str(uuid.uuid4()),
            "time": time,
            "content": content,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **kwargs
        }
        
        data["todos"].append(todo_item)
        
        # 按时间排序
        data["todos"].sort(key=lambda x: x.get("time", ""))
        
        if self._save_todos(date, data):
            return todo_item
        else:
            return {}
    
    def get_todos(self, date: str, status: Optional[str] = None) -> List[Dict]:
        """
        获取指定日期的待办事项
        
        Args:
            date: 日期字符串
            status: 过滤状态（pending/completed/all），默认为all
        
        Returns:
            待办事项列表
        """
        data = self._load_todos(date)
        todos = data.get("todos", [])
        
        if status and status != "all":
            todos = [t for t in todos if t.get("status") == status]
        
        return todos
    
    def get_todos_by_range(self, start_date: str, end_date: str, status: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        获取日期范围内的待办事项
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            status: 过滤状态
        
        Returns:
            {日期: [待办列表]}
        """
        result = {}
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            todos = self.get_todos(date_str, status)
            if todos:
                result[date_str] = todos
            current += timedelta(days=1)
        
        return result
    
    def update_todo_status(self, date: str, todo_id: str, status: str) -> bool:
        """
        更新待办事项状态
        
        Args:
            date: 日期
            todo_id: 待办ID
            status: 新状态
        
        Returns:
            是否成功
        """
        data = self._load_todos(date)
        
        for todo in data["todos"]:
            if todo["id"] == todo_id:
                todo["status"] = status
                todo["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return self._save_todos(date, data)
        
        return False
    
    def delete_todo(self, date: str, todo_id: str) -> bool:
        """
        删除待办事项
        
        Args:
            date: 日期
            todo_id: 待办ID
        
        Returns:
            是否成功
        """
        data = self._load_todos(date)
        
        original_count = len(data["todos"])
        data["todos"] = [t for t in data["todos"] if t["id"] != todo_id]
        
        if len(data["todos"]) < original_count:
            return self._save_todos(date, data)
        
        return False
    
    def search_todos(self, keyword: str, days_range: int = 30) -> Dict[str, List[Dict]]:
        """
        搜索包含关键词的待办事项
        
        Args:
            keyword: 搜索关键词
            days_range: 搜索天数范围（从今天开始往前和往后）
        
        Returns:
            {日期: [匹配的待办列表]}
        """
        result = {}
        
        today = datetime.now()
        
        for i in range(-days_range, days_range + 1):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            todos = self.get_todos(date_str)
            matched = [t for t in todos if keyword.lower() in t["content"].lower()]
            
            if matched:
                result[date_str] = matched
        
        return result
    
    def format_todos_display(self, todos: List[Dict], show_date: bool = False) -> str:
        """
        格式化待办事项显示
        
        Args:
            todos: 待办列表
            show_date: 是否显示日期
        
        Returns:
            格式化的字符串
        """
        if not todos:
            return "📭 没有待办事项"
        
        lines = []
        for i, todo in enumerate(todos, 1):
            status_icon = "✅" if todo["status"] == "completed" else "⏰"
            time_str = todo.get("time", "")
            content = todo.get("content", "")
            
            line = f"{i}. {status_icon} {time_str} - {content}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def get_today_todos(self) -> List[Dict]:
        """获取今天的待办事项"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_todos(today)
    
    def get_upcoming_todos(self, days: int = 7) -> Dict[str, List[Dict]]:
        """
        获取未来几天的待办事项
        
        Args:
            days: 天数
        
        Returns:
            {日期: [待办列表]}
        """
        today = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        return self.get_todos_by_range(today, end_date, status="pending")


# 全局实例
todo_manager = TodoManager()


if __name__ == "__main__":
    # 测试代码
    manager = TodoManager()
    
    # 添加待办
    print("添加待办...")
    todo = manager.add_todo("2024-01-22", "18:00", "给陈龙打电话")
    print(f"✅ 已添加: {todo}")
    
    # 查询待办
    print("\n查询今天的待办...")
    todos = manager.get_todos("2024-01-22")
    print(manager.format_todos_display(todos))
    
    # 搜索待办
    print("\n搜索'陈龙'...")
    results = manager.search_todos("陈龙")
    for date, items in results.items():
        print(f"\n📅 {date}")
        print(manager.format_todos_display(items))
