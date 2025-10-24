"""
增强的 LLM 初始化模块
集成错误处理、性能监控和降级策略
"""

from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from src.core.agent_config import LLM_CONFIG, LLM_CONFIG2, DEFAULT_HEADERS
from src.core.agent_metrics import get_metrics_collector
from src.core.agent_error_handler import get_llm_fallback_handler, LLMType, LLMCallResult


class EnhancedLLM:
    """增强的 LLM 包装器，集成监控和错误处理"""
    
    def __init__(self, config: Dict[str, Any], llm_type: LLMType, name: str):
        self.config = config
        self.llm_type = llm_type
        self.name = name
        self.metrics = get_metrics_collector()
        self.fallback_handler = get_llm_fallback_handler()
        
        # 创建原始 LLM 实例
        self._base_llm = ChatOpenAI(
            model=config["model"],
            base_url=config["base_url"],
            api_key=config["api_key"],
            temperature=config["temperature"],
            default_headers=DEFAULT_HEADERS
        )
        
        # 统计信息
        self.call_count = 0
        self.success_count = 0
        self.total_tokens = {"prompt": 0, "completion": 0, "total": 0}
    
    def invoke(self, messages: List[BaseMessage], context_type: str = "default", 
              max_retries: int = 3) -> Any:
        """
        增强的 LLM 调用方法
        
        Args:
            messages: 消息列表
            context_type: 上下文类型 (question, command_generation, multi_step_planning)
            max_retries: 最大重试次数
            
        Returns:
            LLM 响应结果
        """
        self.call_count += 1
        
        # 使用降级处理器调用 LLM
        result: LLMCallResult = self.fallback_handler.call_llm_with_fallback(
            messages=messages,
            llm_type=self.llm_type,
            context_type=context_type,
            max_retries=max_retries
        )
        
        # 更新统计信息
        if result.success:
            self.success_count += 1
            
            # 更新 Token 统计
            if result.token_usage:
                for key, value in result.token_usage.items():
                    if key == "prompt_tokens":
                        self.total_tokens["prompt"] += value
                    elif key == "completion_tokens":
                        self.total_tokens["completion"] += value
                    elif key == "total_tokens":
                        self.total_tokens["total"] += value
        
        # 创建兼容的响应对象
        class LLMResponse:
            def __init__(self, content: str, token_usage: Optional[Dict] = None):
                self.content = content
                self.usage_metadata = token_usage or {}
                self.response_metadata = {"token_usage": token_usage or {}}
        
        return LLMResponse(result.content, result.token_usage)
    
    def stream(self, messages: List[BaseMessage], context_type: str = "question", 
               max_retries: int = 3):
        """
        流式调用方法（用于打字机效果）
        
        Args:
            messages: 消息列表
            context_type: 上下文类型
            max_retries: 最大重试次数
            
        Yields:
            流式响应块
        """
        self.call_count += 1
        
        # 尝试使用原始 LLM 进行流式调用
        try:
            with self.metrics.measure_operation("llm_stream", self.model_name) as ctx:
                total_content = ""
                
                for chunk in self._base_llm.stream(messages):
                    if hasattr(chunk, "content") and chunk.content:
                        total_content += chunk.content
                    yield chunk
                
                # 记录成功的流式调用
                self.success_count += 1
                ctx["additional_data"] = {"stream_mode": True, "content_length": len(total_content)}
                
        except Exception as e:
            print(f"🚨 流式调用失败: {self.model_name} - {str(e)}")
            
            # 流式调用失败时，降级到普通调用并模拟流式输出
            try:
                result: LLMCallResult = self.fallback_handler.call_llm_with_fallback(
                    messages=messages,
                    llm_type=self.llm_type,
                    context_type=context_type,
                    max_retries=max_retries
                )
                
                if result.success:
                    # 模拟流式输出：将完整响应分块返回
                    content = result.content
                    chunk_size = 5  # 每次返回5个字符
                    
                    for i in range(0, len(content), chunk_size):
                        chunk_content = content[i:i + chunk_size]
                        
                        # 创建模拟的流式响应块
                        class StreamChunk:
                            def __init__(self, content: str):
                                self.content = content
                        
                        yield StreamChunk(chunk_content)
                else:
                    # 如果降级也失败，返回错误信息
                    class StreamChunk:
                        def __init__(self, content: str):
                            self.content = content
                    
                    yield StreamChunk(result.content)
                    
            except Exception as fallback_error:
                print(f"🚨 降级流式调用也失败: {str(fallback_error)}")
                
                # 最终降级：返回错误信息
                class StreamChunk:
                    def __init__(self, content: str):
                        self.content = content
                
                yield StreamChunk("抱歉，AI 服务暂时不可用，请稍后重试。")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取 LLM 统计信息"""
        success_rate = self.success_count / max(self.call_count, 1)
        
        return {
            "name": self.name,
            "model": self.config["model"],
            "call_count": self.call_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "total_tokens": self.total_tokens.copy()
        }
    
    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config["model"]


# 创建增强的 LLM 实例
llm = EnhancedLLM(LLM_CONFIG, LLMType.PRIMARY, "通用LLM")
llm_code = EnhancedLLM(LLM_CONFIG2, LLMType.SECONDARY, "代码LLM")


def get_llm_stats() -> Dict[str, Any]:
    """获取所有 LLM 的统计信息"""
    return {
        "primary_llm": llm.get_stats(),
        "secondary_llm": llm_code.get_stats(),
        "session_summary": {
            "total_calls": llm.call_count + llm_code.call_count,
            "total_tokens": {
                "prompt": llm.total_tokens["prompt"] + llm_code.total_tokens["prompt"],
                "completion": llm.total_tokens["completion"] + llm_code.total_tokens["completion"],
                "total": llm.total_tokens["total"] + llm_code.total_tokens["total"]
            }
        }
    }


def reset_llm_stats():
    """重置 LLM 统计信息"""
    llm.call_count = 0
    llm.success_count = 0
    llm.total_tokens = {"prompt": 0, "completion": 0, "total": 0}
    
    llm_code.call_count = 0
    llm_code.success_count = 0
    llm_code.total_tokens = {"prompt": 0, "completion": 0, "total": 0}
