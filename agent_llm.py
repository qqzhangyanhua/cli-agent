"""
LLM初始化模块
"""

from langchain_openai import ChatOpenAI
from agent_config import LLM_CONFIG, LLM_CONFIG2, DEFAULT_HEADERS


# 通用LLM - 用于意图分析、问答等
llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
    default_headers=DEFAULT_HEADERS
)

# 代码生成专用LLM - 用于生成命令和代码
llm_code = ChatOpenAI(
    model=LLM_CONFIG2["model"],
    base_url=LLM_CONFIG2["base_url"],
    api_key=LLM_CONFIG2["api_key"],
    temperature=LLM_CONFIG2["temperature"],
    default_headers=DEFAULT_HEADERS
)
