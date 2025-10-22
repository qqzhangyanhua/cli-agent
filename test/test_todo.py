"""
测试待办事项功能
"""

import sys
import os
from pathlib import Path

# 添加项目目录到Python路径
PROJECT_DIR = Path(__file__).parent.parent.absolute()
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from todo_manager import TodoManager
from datetime import datetime


def test_todo_manager():
    """测试待办事项管理器"""
    
    print("=" * 60)
    print("测试待办事项管理器")
    print("=" * 60)
    
    # 创建测试实例
    manager = TodoManager(todos_dir="test_todos")
    
    # 1. 添加待办
    print("\n1. 测试添加待办...")
    today = datetime.now().strftime("%Y-%m-%d")
    todo1 = manager.add_todo(today, "18:00", "给陈龙打电话")
    print(f"✅ 添加成功: {todo1['content']} - {todo1['time']}")
    
    todo2 = manager.add_todo(today, "14:30", "参加会议")
    print(f"✅ 添加成功: {todo2['content']} - {todo2['time']}")
    
    todo3 = manager.add_todo(today, "", "复习英语")
    print(f"✅ 添加成功: {todo3['content']}")
    
    # 2. 查询今天的待办
    print("\n2. 测试查询今天的待办...")
    todos = manager.get_today_todos()
    print(f"找到 {len(todos)} 个待办:")
    print(manager.format_todos_display(todos))
    
    # 3. 搜索待办
    print("\n3. 测试搜索待办...")
    results = manager.search_todos("陈龙", days_range=7)
    print(f"搜索「陈龙」:")
    for date, items in results.items():
        print(f"\n📅 {date}")
        print(manager.format_todos_display(items))
    
    # 4. 更新状态
    print("\n4. 测试更新待办状态...")
    success = manager.update_todo_status(today, todo1['id'], "completed")
    if success:
        print(f"✅ 更新成功")
        todos = manager.get_today_todos()
        print(manager.format_todos_display(todos))
    
    # 5. 删除待办
    print("\n5. 测试删除待办...")
    success = manager.delete_todo(today, todo2['id'])
    if success:
        print(f"✅ 删除成功")
        todos = manager.get_today_todos()
        print(f"剩余 {len(todos)} 个待办:")
        print(manager.format_todos_display(todos))
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 清理测试文件
    import shutil
    if os.path.exists("test_todos"):
        shutil.rmtree("test_todos")
        print("\n✅ 测试文件已清理")


if __name__ == "__main__":
    test_todo_manager()
