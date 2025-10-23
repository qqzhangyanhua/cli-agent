"""
测试 Git 自动提交工作流
演示完整的 git add -> 生成commit消息 -> git commit 流程
"""

import sys
from agent_workflow import build_agent
from agent_config import AgentState

def test_auto_commit_workflow():
    """测试完整的 Git 自动提交工作流"""
    
    print("=" * 80)
    print("🧪 测试 Git 自动提交工作流")
    print("=" * 80)
    
    # 构建智能体
    print("\n📦 构建智能体工作流...")
    agent = build_agent()
    print("✅ 工作流构建完成")
    
    # 测试场景
    test_cases = [
        {
            "name": "测试1: 提交代码（完整流程）",
            "input": "提交代码",
            "description": "应该执行 git add -> 生成消息 -> git commit"
        },
        {
            "name": "测试2: 一键提交",
            "input": "一键提交",
            "description": "应该执行完整的提交流程"
        },
        {
            "name": "测试3: 生成并提交commit",
            "input": "生成并提交commit",
            "description": "应该执行完整的提交流程"
        },
        {
            "name": "测试4: 自动提交",
            "input": "自动提交",
            "description": "应该执行完整的提交流程"
        }
    ]
    
    # 只测试第一个场景
    test_case = test_cases[0]
    
    print(f"\n{'='*80}")
    print(f"📝 {test_case['name']}")
    print(f"💬 用户输入: {test_case['input']}")
    print(f"📋 预期行为: {test_case['description']}")
    print(f"{'='*80}\n")
    
    try:
        # 初始化状态
        initial_state: AgentState = {
            "user_input": test_case['input'],
            "intent": "unknown",
            "command": "",
            "commands": [],
            "command_output": "",
            "command_outputs": [],
            "response": "",
            "error": "",
            "needs_file_creation": False,
            "file_path": "",
            "file_content": "",
            "chat_history": [],
            "mcp_tool": "",
            "mcp_params": {},
            "mcp_result": "",
            "original_input": "",
            "referenced_files": [],
            "file_contents": {},
            "todo_action": "",
            "todo_date": "",
            "todo_time": "",
            "todo_content": "",
            "todo_result": "",
            "data_conversion_type": "",
            "source_format": "",
            "target_format": "",
            "conversion_result": "",
            "diagnostic_result": "",
            # Git 自动提交相关字段
            "git_add_success": False,
            "git_files_count": 0,
            "git_commit_message_generated": False,
            "git_commit_message": "",
            "git_file_stats": "",
            "git_commit_success": False,
            "git_commit_hash": ""
        }
        
        # 执行工作流
        print("🚀 开始执行工作流...\n")
        result = agent.invoke(initial_state)
        
        # 显示结果
        print(f"\n{'='*80}")
        print(f"📊 执行结果")
        print(f"{'='*80}")
        
        print(f"\n✅ 意图识别: {result.get('intent', 'unknown')}")
        
        if result.get('intent') == 'auto_commit':
            print(f"\n📦 Git Add 状态: {'✅ 成功' if result.get('git_add_success') else '❌ 失败'}")
            if result.get('git_add_success'):
                print(f"   暂存文件数: {result.get('git_files_count', 0)} 个")
            
            print(f"\n💡 Commit 消息生成: {'✅ 成功' if result.get('git_commit_message_generated') else '❌ 失败'}")
            if result.get('git_commit_message_generated'):
                print(f"   生成的消息: {result.get('git_commit_message', 'N/A')}")
            
            print(f"\n✍️  Git Commit 状态: {'✅ 成功' if result.get('git_commit_success') else '❌ 失败'}")
            if result.get('git_commit_success'):
                commit_hash = result.get('git_commit_hash', '')
                if commit_hash:
                    print(f"   Commit Hash: {commit_hash[:7]}")
        
        print(f"\n📄 最终响应:")
        print(f"{'─'*80}")
        print(result.get('response', '无响应'))
        print(f"{'─'*80}")
        
        if result.get('error'):
            print(f"\n❌ 错误信息: {result['error']}")
        
        print(f"\n{'='*80}")
        print(f"✅ 测试完成")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_workflow_info():
    """显示工作流信息"""
    print("\n" + "=" * 80)
    print("📚 Git 自动提交工作流说明")
    print("=" * 80)
    
    print("""
🎯 工作流程:

  用户输入: "提交代码" / "一键提交" / "自动提交" / "生成并提交commit"
     ↓
  [文件引用处理] 解析 @ 文件引用（如果有）
     ↓
  [工具调用] LLM 识别意图 → auto_commit
     ↓
  [路由] 根据意图 auto_commit → git_add 节点
     ↓
  [Git Add 节点] 执行 git add .
     ├─ 成功 → 继续
     └─ 失败 → 结束（显示错误）
     ↓
  [生成 Commit 消息节点] 
     • 分析 git diff
     • 使用 LLM（代码模型）生成 commit 消息
     ├─ 成功 → 继续
     └─ 失败 → 结束（显示错误）
     ↓
  [执行 Commit 节点] 执行 git commit -m "消息"
     ├─ 成功 → 显示完整结果
     └─ 失败 → 显示错误和手动命令
     ↓
  [结束] 返回最终响应

✨ 特性:
  • 完全自动化：一条命令完成三个步骤
  • 智能生成：LLM 分析代码变更生成高质量 commit 消息
  • 错误处理：每步都有错误检查和友好提示
  • 状态追踪：使用 LangGraph State 追踪每个步骤的状态
  • 多步骤工作流：充分利用 LangGraph 的节点和路由机制

🔧 与现有功能的区别:
  • generate_commit: 只生成 commit 消息，不执行提交
  • auto_commit: 执行完整流程（add + 生成 + commit）

📝 使用方式:
  1. 命令行: ./ai-agent
  2. 输入: "提交代码" 或 "一键提交"
  3. 等待: 自动执行所有步骤
  4. 完成: 查看提交结果
""")
    
    print("=" * 80)


if __name__ == "__main__":
    # 显示工作流信息
    show_workflow_info()
    
    # 执行测试
    success = test_auto_commit_workflow()
    
    sys.exit(0 if success else 1)

