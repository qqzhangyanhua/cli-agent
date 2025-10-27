"""
问题回答节点
提供流式打字机效果的问答功能
"""

import time
import threading
from queue import Queue
from langchain_core.messages import HumanMessage

from src.core.agent_config import AgentState, LLM_CONFIG
from src.core.agent_memory import memory
from src.core.agent_llm import llm


def question_answerer(state: AgentState) -> dict:
    """回答用户问题（打字机效果流式输出）"""
    user_input = state["user_input"]
    context = memory.get_context_string()
    recent_commands = memory.get_recent_commands()

    prompt = f"""你是一个友好的AI终端助手。回答用户问题，并利用对话历史提供更好的帮助。

{context}

{recent_commands}

当前问题: {user_input}

请简洁但全面地回答用户的问题。如果用户提到\"刚才\"、\"之前\"等词，请参考对话历史。

回答:"""

    print(f"[问题回答] 生成回答")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print()  # 空行
    print("─" * 80)
    print("🤖 助手: ", end="", flush=True)

    # 打字机效果流式输出
    try:
        response = ""
        char_queue = Queue()
        output_finished = threading.Event()

        def typewriter_output():
            """打字机输出线程"""
            while not output_finished.is_set() or not char_queue.empty():
                try:
                    # 从队列获取字符，超时避免死锁
                    char = char_queue.get(timeout=0.1)
                    print(char, end="", flush=True)

                    # 智能打字机延迟
                    if char in '，。！？；：':  # 标点符号稍微停顿
                        time.sleep(0.06)
                    elif char == ' ':  # 空格快速跳过
                        time.sleep(0.01)
                    else:  # 普通字符
                        time.sleep(0.03)

                except:
                    continue

        # 启动打字机输出线程
        output_thread = threading.Thread(target=typewriter_output, daemon=True)
        output_thread.start()

        # 收集LLM输出并逐字符放入队列
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            if hasattr(chunk, "content") and chunk.content:
                content = chunk.content
                response += content

                # 逐字符放入队列
                for char in content:
                    char_queue.put(char)

        # 标记输出完成
        output_finished.set()

        # 等待输出线程完成
        output_thread.join(timeout=5.0)  # 最多等待5秒

        # 确保所有字符都输出完毕
        while not char_queue.empty():
            try:
                char = char_queue.get_nowait()
                print(char, end="", flush=True)
            except:
                break

        print()  # 换行
        print("─" * 80)

        return {"response": response}

    except Exception as e:
        error_msg = f"❌ 生成回答失败: {str(e)}"
        print(error_msg)
        print("─" * 80)
        return {"response": error_msg, "error": str(e)}
