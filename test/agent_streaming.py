"""
流式输出支持模块
提供流式 LLM 调用和实时输出功能
"""

import sys
from typing import Iterator, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from agent_llm import llm


def stream_llm_response(messages: list, print_output: bool = True) -> tuple[str, str]:
    """
    流式调用 LLM 并实时输出

    Args:
        messages: 消息列表
        print_output: 是否实时打印输出

    Returns:
        (完整响应文本, 错误信息)
    """
    try:
        full_response = ""

        if print_output:
            print("🤖 助手: ", end="", flush=True)

        # 使用 stream 方法进行流式调用
        for chunk in llm.stream(messages):
            # 提取内容
            if hasattr(chunk, 'content'):
                content = chunk.content
            elif isinstance(chunk, str):
                content = chunk
            else:
                content = str(chunk)

            # 累积完整响应
            full_response += content

            # 实时输出
            if print_output:
                print(content, end="", flush=True)

        if print_output:
            print()  # 换行

        return full_response, ""

    except Exception as e:
        error_msg = f"流式调用失败: {str(e)}"
        if print_output:
            print(f"\n❌ {error_msg}")
        return "", error_msg


def stream_llm_with_prompt(prompt: str, print_output: bool = True) -> tuple[str, str]:
    """
    便捷函数：使用提示词进行流式调用

    Args:
        prompt: 提示词
        print_output: 是否实时打印

    Returns:
        (完整响应, 错误信息)
    """
    messages = [HumanMessage(content=prompt)]
    return stream_llm_response(messages, print_output)


def print_streaming(text: str, prefix: str = "", color_code: str = ""):
    """
    流式打印文本（模拟打字机效果）

    Args:
        text: 要打印的文本
        prefix: 前缀（如 "🤖 助手: "）
        color_code: ANSI 颜色代码（可选）
    """
    import time

    if prefix:
        print(prefix, end="", flush=True)

    for char in text:
        if color_code:
            print(f"{color_code}{char}\033[0m", end="", flush=True)
        else:
            print(char, end="", flush=True)

        # 根据字符类型调整延迟
        if char in "。！？\n":
            time.sleep(0.05)  # 标点符号后稍微停顿
        elif char in "，、；：":
            time.sleep(0.03)
        else:
            time.sleep(0.01)  # 普通字符快速输出

    print()  # 结束换行


def format_streaming_output(content: str, role: str = "assistant") -> None:
    """
    格式化流式输出

    Args:
        content: 输出内容
        role: 角色（assistant/user/system）
    """
    if role == "assistant":
        print("─" * 80)
        print("🤖 助手: ", end="", flush=True)
    elif role == "user":
        print("👤 你: ", end="", flush=True)

    print(content)

    if role == "assistant":
        print("─" * 80)


# 测试代码
if __name__ == "__main__":
    print("测试流式输出功能\n")

    # 测试1：流式问答
    print("=" * 60)
    print("测试1: 流式问答")
    print("=" * 60)

    response, error = stream_llm_with_prompt(
        "用一句话解释什么是 Python",
        print_output=True
    )

    if not error:
        print(f"\n✅ 完整响应长度: {len(response)} 字符")

    # 测试2：不打印模式
    print("\n" + "=" * 60)
    print("测试2: 不打印模式（后台处理）")
    print("=" * 60)

    response2, error2 = stream_llm_with_prompt(
        "什么是 Git",
        print_output=False
    )

    if not error2:
        print(f"✅ 后台获取响应: {response2[:100]}...")
        print(f"   完整长度: {len(response2)} 字符")
