"""
Code Review 工具 - LangChain Tool 封装
基于 git diff 进行代码审查，发现潜在问题并按严重性分级
"""

from langchain_core.tools import Tool
from src.tools.git_tools import git_tools
from src.core.agent_llm import llm_code
from src.core.agent_config import LLM_CONFIG2
from langchain_core.messages import HumanMessage
from typing import Dict, List


def analyze_code_changes() -> Dict:
    """
    分析代码变更，包含 staged 和 unstaged 的所有修改
    
    Returns:
        {
            "success": bool,
            "diff_content": str,
            "files_changed": list,
            "summary": str,
            "error": str
        }
    """
    # 获取 unstaged 和 staged 的 diff
    unstaged_diff = git_tools.get_git_diff(staged=False)
    staged_diff = git_tools.get_git_diff(staged=True)
    
    # 合并 diff 内容
    diff_parts = []
    all_files = []
    
    if staged_diff.get("has_diff"):
        diff_parts.append(f"=== 已暂存的变更 (Staged Changes) ===\n{staged_diff['diff']}")
        all_files.extend(staged_diff.get("files_changed", []))
    
    if unstaged_diff.get("has_diff"):
        diff_parts.append(f"=== 未暂存的变更 (Unstaged Changes) ===\n{unstaged_diff['diff']}")
        all_files.extend(unstaged_diff.get("files_changed", []))
    
    if not diff_parts:
        return {
            "success": False,
            "error": "⚠️ 没有代码变更，无需进行 code review"
        }
    
    # 去重文件列表
    all_files = list(set(all_files))
    
    diff_content = "\n\n".join(diff_parts)
    
    summary = f"共 {len(all_files)} 个文件有变更"
    if staged_diff.get("has_diff"):
        summary += f"（已暂存：{len(staged_diff.get('files_changed', []))} 个）"
    if unstaged_diff.get("has_diff"):
        summary += f"（未暂存：{len(unstaged_diff.get('files_changed', []))} 个）"
    
    return {
        "success": True,
        "diff_content": diff_content,
        "files_changed": all_files,
        "summary": summary
    }


def perform_code_review_func(input_str: str = "") -> str:
    """
    执行代码审查
    
    Args:
        input_str: 可选的额外说明（通常不需要）
    
    Returns:
        格式化的代码审查报告
    """
    try:
        print(f"[Code Review] 开始代码审查...")
        
        # 检查是否是 Git 仓库
        if not git_tools.check_git_repo():
            error_msg = "❌ 当前目录不是 Git 仓库"
            print(f"[Code Review] {error_msg}")
            return error_msg
        
        # 分析代码变更
        analysis = analyze_code_changes()
        
        if not analysis["success"]:
            error_msg = analysis.get('error', 'Code review 失败')
            print(f"[Code Review] {error_msg}")
            return error_msg
        
        print(f"[Code Review] ✅ 分析完成")
        print(f"[Code Review] {analysis['summary']}")
        print(f"[Code Review] 变更文件: {len(analysis['files_changed'])} 个")
        
        # 截取 diff（避免太长）
        diff_content = analysis['diff_content']
        max_diff_length = 10000  # 增加长度以便更详细分析
        if len(diff_content) > max_diff_length:
            diff_content = diff_content[:max_diff_length] + "\n\n... (diff太长，已截断)"
        
        # 构建 Code Review prompt
        prompt = f"""你是一个专业的代码审查专家。你的任务是仔细审查代码变更，发现潜在问题，并按严重性分级。

📄 **代码变更内容**:
```diff
{diff_content}
```

📁 **变更的文件列表** ({len(analysis['files_changed'])}个):
{chr(10).join(['  - ' + f for f in analysis['files_changed']])}

🎯 **审查任务**:

请仔细分析上面的代码变更（diff），从以下维度进行审查：

**1. 安全性 (Security)**
- 是否存在安全漏洞（SQL注入、XSS、CSRF等）
- 敏感信息是否暴露（密码、密钥、token等）
- 权限控制是否正确
- 输入验证是否充分

**2. 性能 (Performance)**
- 是否存在性能问题（死循环、O(n²)算法等）
- 数据库查询是否优化（N+1问题、缺少索引）
- 内存泄漏风险
- 不必要的计算或重复操作

**3. 代码质量 (Code Quality)**
- 逻辑错误或潜在bug
- 异常处理是否完善
- 边界条件处理
- 代码重复（DRY原则）
- 函数复杂度过高

**4. 最佳实践 (Best Practices)**
- 命名规范（变量、函数、类名）
- 代码注释和文档
- 类型注解（Python）
- 代码结构和组织
- 测试覆盖

**5. 代码风格 (Code Style)**
- 格式和缩进
- 导入语句顺序
- 行长度
- 空格和换行

📊 **问题严重性分级**:

🔴 **严重问题 (Critical)** - 必须立即修复
- 安全漏洞
- 关键bug（会导致崩溃、数据丢失）
- 破坏性变更（breaking changes）
- 严重的性能问题

🟡 **中级问题 (Medium)** - 建议修复
- 潜在bug（边界情况）
- 性能优化建议
- 代码质量问题
- 违反最佳实践
- 缺少错误处理

🟢 **普通问题 (Minor)** - 可选修复
- 代码风格问题
- 命名建议
- 代码优化建议
- 注释和文档改进

📋 **输出格式要求**:

请按以下格式输出代码审查报告：

```
📊 代码审查概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 审查文件: {len(analysis['files_changed'])} 个
• 发现问题: X 个（🔴严重 A个，🟡中级 B个，🟢普通 C个）
• 审查结论: [通过/需要修改/存在严重问题]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 严重问题 (A个)

1. [文件名:行号或函数名] 问题类型
   
   问题描述：
   详细说明发现的问题
   
   影响：
   说明这个问题可能造成的影响
   
   建议：
   提供具体的修复建议和代码示例（如果适用）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟡 中级问题 (B个)

1. [文件名:行号或函数名] 问题类型
   
   问题描述：
   ...
   
   建议：
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 普通问题 (C个)

1. [文件名:行号或函数名] 问题类型
   
   问题描述：
   ...
   
   建议：
   ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 表现良好的方面

• 列出代码中做得好的地方
• 值得保持的良好实践
• ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 总体建议

1. 提供整体的改进建议
2. 优先级排序
3. ...
```

⚠️ **重要提醒**:
1. **基于实际diff内容分析**，不要臆测没有看到的代码
2. **提供具体位置**（文件名、函数名、行号）
3. **给出可操作的建议**，不要只说"需要改进"
4. **如果没有发现问题**，说明"代码质量良好，未发现明显问题"
5. **关注变更部分**，不要审查未变更的代码

现在请开始代码审查，只返回审查报告内容:"""

        print(f"[Code Review] 使用模型: {LLM_CONFIG2['model']}")
        print(f"[Code Review] 正在生成审查报告...")
        
        # 调用 LLM 生成代码审查报告
        result = llm_code.invoke([HumanMessage(content=prompt)])
        review_report = result.content.strip()
        
        # 清理可能的 markdown 格式
        if review_report.startswith("```"):
            lines = review_report.split('\n')
            # 移除首尾的 ``` 标记
            if lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            review_report = '\n'.join(lines)
        
        print(f"[Code Review] ✅ 审查完成")
        
        # 格式化最终响应
        response = "📝 代码审查报告已生成\n\n"
        response += review_report
        
        return response
    
    except Exception as e:
        error_msg = f"❌ 代码审查失败: {str(e)}"
        print(f"[Code Review] {error_msg}")
        return error_msg


# 创建 LangChain Tool 实例
code_review_tool = Tool(
    name="code_review",
    description="""对当前代码变更进行代码审查（Code Review）。

适用场景:
- "对当前代码进行code review"
- "代码审查"
- "检查我的代码"
- "帮我review一下代码"
- "代码有什么问题吗"

此工具会:
1. 自动获取 git diff（包括 staged 和 unstaged 的所有变更）
2. 使用 LLM 深度分析代码，发现潜在问题
3. 按严重性分级：🔴 严重、🟡 中级、🟢 普通
4. 提供具体的改进建议

不需要任何参数输入。""",
    func=perform_code_review_func
)


# 导出工具
code_review_tools = [code_review_tool]


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("🔍 Code Review 工具测试")
    print("=" * 80)
    
    # 测试代码审查功能
    result = perform_code_review_func()
    print("\n" + "=" * 80)
    print("📋 审查结果:")
    print("=" * 80)
    print(result)
    print("=" * 80)
    print("测试完成！")

