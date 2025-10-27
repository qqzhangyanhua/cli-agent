"""
健壮的 JSON 提取与解析工具
用于从 LLM 输出中提取 JSON 片段并安全解析
"""

import json
import re
from typing import Tuple, Any, Optional


def extract_json_str(text: str) -> str:
    """从混合文本中尽力提取 JSON 字符串。

    策略：
    1) 优先匹配 ```json fenced block
    2) 次选 ``` fenced block
    3) 基于括号配对找到第一个 {} 或 [] 的完整片段
    """
    if not text:
        return ""

    # 1) ```json ... ```
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 2) ``` ... ```
    m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 3) 括号配对查找对象或数组
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1].strip()
    return text.strip()


def safe_json_loads(text: str) -> Tuple[Optional[Any], Optional[str]]:
    """安全解析 JSON，返回 (对象, 错误信息)。"""
    try:
        return json.loads(text), None
    except Exception as e:
        return None, str(e)

