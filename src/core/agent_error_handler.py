"""
LLM 错误处理和降级策略模块
专门处理 LLM 调用失败的各种情况
"""

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from src.core.agent_config import LLM_CONFIG, LLM_CONFIG2, DEFAULT_HEADERS
from src.core.agent_resilience import ErrorContext, ErrorType, FallbackResult, FallbackStrategy
from src.core.agent_metrics import get_metrics_collector


class LLMType(Enum):
    """LLM 类型枚举"""
    PRIMARY = "primary"    # 主要模型 (Kimi)
    SECONDARY = "secondary"  # 备用模型 (Claude)


@dataclass
class LLMCallResult:
    """LLM 调用结果"""
    success: bool
    content: str
    model_used: str
    token_usage: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None
    fallback_used: bool = False
    strategy_used: Optional[FallbackStrategy] = None


class LLMFallbackHandler:
    """LLM 降级处理器"""
    
    def __init__(self):
        self.metrics = get_metrics_collector()
        
        # 初始化两个 LLM 实例
        self.primary_llm = ChatOpenAI(
            model=LLM_CONFIG["model"],
            base_url=LLM_CONFIG["base_url"],
            api_key=LLM_CONFIG["api_key"],
            temperature=LLM_CONFIG["temperature"],
            default_headers=DEFAULT_HEADERS
        )
        
        self.secondary_llm = ChatOpenAI(
            model=LLM_CONFIG2["model"],
            base_url=LLM_CONFIG2["base_url"],
            api_key=LLM_CONFIG2["api_key"],
            temperature=LLM_CONFIG2["temperature"],
            default_headers=DEFAULT_HEADERS
        )
        
        # 模板响应库
        self.response_templates = {
            "question": "抱歉，AI 服务暂时不可用。我已记录您的问题，请稍后重试。",
            "command_generation": "抱歉，无法生成命令。请手动执行相关操作。",
            "multi_step_planning": "抱歉，无法制定执行计划。请将任务分解为更简单的步骤。",
            "default": "抱歉，AI 服务暂时不可用，请稍后重试。"
        }
        
        # 降级策略配置
        self.fallback_strategies = [
            self._retry_with_exponential_backoff,
            self._switch_to_backup_model,
            self._use_simplified_prompt,
            self._use_template_response
        ]
    
    def call_llm_with_fallback(self, messages: List, llm_type: LLMType = LLMType.PRIMARY, 
                              context_type: str = "default", max_retries: int = 3) -> LLMCallResult:
        """
        带降级策略的 LLM 调用
        
        Args:
            messages: 消息列表
            llm_type: LLM 类型
            context_type: 上下文类型 (question, command_generation, multi_step_planning)
            max_retries: 最大重试次数
            
        Returns:
            LLM 调用结果
        """
        # 选择初始 LLM
        current_llm = self.primary_llm if llm_type == LLMType.PRIMARY else self.secondary_llm
        model_name = LLM_CONFIG["model"] if llm_type == LLMType.PRIMARY else LLM_CONFIG2["model"]
        
        # 创建错误上下文
        error_context = ErrorContext(
            error_type=ErrorType.LLM_CALL_FAILED,
            error_message="",
            node_name="llm_call",
            user_input=str(messages),
            operation_name="llm_call"
        )
        
        # 尝试直接调用
        with self.metrics.measure_operation("llm_call", model_name) as ctx:
            try:
                result = current_llm.invoke(messages)
                
                # 提取 Token 使用信息
                token_usage = self._extract_token_usage(result)
                ctx["token_usage"] = token_usage
                
                return LLMCallResult(
                    success=True,
                    content=result.content,
                    model_used=model_name,
                    token_usage=token_usage
                )
                
            except Exception as e:
                error_context.error_message = str(e)
                print(f"🚨 LLM 调用失败: {model_name} - {str(e)}")
                
                # 执行降级策略
                return self._execute_fallback_strategies(
                    messages, error_context, context_type, max_retries
                )
    
    def _execute_fallback_strategies(self, messages: List, error_context: ErrorContext, 
                                   context_type: str, max_retries: int) -> LLMCallResult:
        """执行降级策略链"""
        
        for i, strategy in enumerate(self.fallback_strategies):
            try:
                print(f"🔄 尝试降级策略 {i+1}: {strategy.__name__}")
                
                result = strategy(messages, error_context, context_type, max_retries)
                
                if result.success:
                    print(f"✅ 降级策略成功: {strategy.__name__}")
                    result.fallback_used = True
                    return result
                else:
                    print(f"❌ 降级策略失败: {strategy.__name__} - {result.error_message}")
                    
            except Exception as e:
                print(f"⚠️ 降级策略异常: {strategy.__name__} - {str(e)}")
                continue
        
        # 所有策略都失败，返回最终降级
        return self._final_fallback(error_context, context_type)
    
    def _retry_with_exponential_backoff(self, messages: List, error_context: ErrorContext, 
                                      context_type: str, max_retries: int) -> LLMCallResult:
        """指数退避重试策略"""
        
        for attempt in range(max_retries):
            if attempt > 0:
                # 计算延迟时间
                delay = min(2 ** attempt + random.uniform(0, 1), 30)  # 最大30秒
                print(f"⏱️ 重试延迟: {delay:.1f}s (第 {attempt + 1} 次)")
                time.sleep(delay)
            
            try:
                # 重新尝试原始 LLM
                with self.metrics.measure_operation("llm_call_retry", "retry") as ctx:
                    result = self.primary_llm.invoke(messages)
                    token_usage = self._extract_token_usage(result)
                    ctx["token_usage"] = token_usage
                    
                    return LLMCallResult(
                        success=True,
                        content=result.content,
                        model_used=LLM_CONFIG["model"],
                        token_usage=token_usage,
                        strategy_used=FallbackStrategy.RETRY_WITH_BACKOFF
                    )
                    
            except Exception as e:
                print(f"❌ 重试失败 (第 {attempt + 1} 次): {str(e)}")
                if attempt == max_retries - 1:
                    return LLMCallResult(
                        success=False,
                        content="",
                        model_used=LLM_CONFIG["model"],
                        error_message=f"重试 {max_retries} 次后仍然失败: {str(e)}"
                    )
        
        return LLMCallResult(success=False, content="", model_used="", error_message="重试失败")
    
    def _switch_to_backup_model(self, messages: List, error_context: ErrorContext, 
                              context_type: str, max_retries: int) -> LLMCallResult:
        """切换到备用模型策略"""
        
        try:
            print(f"🔄 切换到备用模型: {LLM_CONFIG2['model']}")
            
            with self.metrics.measure_operation("llm_call_backup", LLM_CONFIG2["model"]) as ctx:
                result = self.secondary_llm.invoke(messages)
                token_usage = self._extract_token_usage(result)
                ctx["token_usage"] = token_usage
                
                return LLMCallResult(
                    success=True,
                    content=result.content,
                    model_used=LLM_CONFIG2["model"],
                    token_usage=token_usage,
                    strategy_used=FallbackStrategy.SWITCH_MODEL
                )
                
        except Exception as e:
            return LLMCallResult(
                success=False,
                content="",
                model_used=LLM_CONFIG2["model"],
                error_message=f"备用模型也失败: {str(e)}"
            )
    
    def _use_simplified_prompt(self, messages: List, error_context: ErrorContext, 
                             context_type: str, max_retries: int) -> LLMCallResult:
        """使用简化提示策略"""
        
        try:
            # 简化消息内容
            simplified_messages = self._simplify_messages(messages, context_type)
            
            print(f"🔄 使用简化提示 (长度: {len(str(simplified_messages))})")
            
            with self.metrics.measure_operation("llm_call_simplified", "simplified") as ctx:
                # 先尝试备用模型
                result = self.secondary_llm.invoke(simplified_messages)
                token_usage = self._extract_token_usage(result)
                ctx["token_usage"] = token_usage
                
                return LLMCallResult(
                    success=True,
                    content=result.content,
                    model_used=LLM_CONFIG2["model"],
                    token_usage=token_usage,
                    strategy_used=FallbackStrategy.USE_TEMPLATE
                )
                
        except Exception as e:
            return LLMCallResult(
                success=False,
                content="",
                model_used="simplified",
                error_message=f"简化提示失败: {str(e)}"
            )
    
    def _use_template_response(self, messages: List, error_context: ErrorContext, 
                             context_type: str, max_retries: int) -> LLMCallResult:
        """使用模板响应策略"""
        
        template = self.response_templates.get(context_type, self.response_templates["default"])
        
        # 尝试根据用户输入定制模板
        try:
            if messages and hasattr(messages[-1], 'content'):
                user_content = messages[-1].content.lower()
                
                if any(word in user_content for word in ["命令", "执行", "运行"]):
                    template = self.response_templates.get("command_generation", template)
                elif any(word in user_content for word in ["计划", "步骤", "如何"]):
                    template = self.response_templates.get("multi_step_planning", template)
                elif any(word in user_content for word in ["什么", "为什么", "怎么", "?"]):
                    template = self.response_templates.get("question", template)
        except:
            pass  # 如果定制失败，使用默认模板
        
        return LLMCallResult(
            success=True,
            content=template,
            model_used="template",
            strategy_used=FallbackStrategy.USE_TEMPLATE
        )
    
    def _final_fallback(self, error_context: ErrorContext, context_type: str) -> LLMCallResult:
        """最终降级策略"""
        
        final_message = f"""
⚠️ AI 服务暂时不可用

所有降级策略都已尝试，但仍无法提供服务。

错误信息: {error_context.error_message}
时间: {error_context.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

建议:
• 检查网络连接
• 稍后重试
• 如问题持续，请联系管理员

您的请求已被记录，我们会尽快处理。
"""
        
        return LLMCallResult(
            success=True,
            content=final_message,
            model_used="fallback",
            strategy_used=FallbackStrategy.GRACEFUL_DEGRADATION
        )
    
    def _simplify_messages(self, messages: List, context_type: str) -> List:
        """简化消息内容"""
        
        simplified = []
        
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
                
                # 根据上下文类型简化
                if context_type == "command_generation":
                    # 保留关键信息，移除详细说明
                    content = self._extract_command_keywords(content)
                elif context_type == "question":
                    # 保留问题核心，移除冗余信息
                    content = self._extract_question_core(content)
                elif context_type == "multi_step_planning":
                    # 保留任务描述，移除详细要求
                    content = self._extract_task_description(content)
                
                # 限制长度
                if len(content) > 500:
                    content = content[:500] + "..."
                
                # 创建简化的消息
                if isinstance(msg, HumanMessage):
                    simplified.append(HumanMessage(content=content))
                elif isinstance(msg, AIMessage):
                    simplified.append(AIMessage(content=content))
        
        return simplified
    
    def _extract_command_keywords(self, content: str) -> str:
        """提取命令相关关键词"""
        keywords = ["列出", "显示", "查看", "创建", "删除", "运行", "执行", "安装", "启动", "停止"]
        
        lines = content.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(keyword in line for keyword in keywords):
                relevant_lines.append(line)
        
        return '\n'.join(relevant_lines) if relevant_lines else content[:200]
    
    def _extract_question_core(self, content: str) -> str:
        """提取问题核心"""
        question_words = ["什么", "为什么", "怎么", "如何", "哪里", "什么时候", "?", "？"]
        
        sentences = content.split('。')
        question_sentences = []
        
        for sentence in sentences:
            if any(word in sentence for word in question_words):
                question_sentences.append(sentence)
        
        return '。'.join(question_sentences) if question_sentences else content[:200]
    
    def _extract_task_description(self, content: str) -> str:
        """提取任务描述"""
        task_words = ["需要", "想要", "希望", "计划", "准备", "打算"]
        
        lines = content.split('\n')
        task_lines = []
        
        for line in lines:
            if any(word in line for word in task_words):
                task_lines.append(line)
        
        return '\n'.join(task_lines) if task_lines else content[:200]
    
    def _extract_token_usage(self, result) -> Optional[Dict[str, int]]:
        """提取 Token 使用信息"""
        try:
            if hasattr(result, 'usage_metadata') and result.usage_metadata:
                return {
                    "prompt_tokens": result.usage_metadata.get('input_tokens', 0),
                    "completion_tokens": result.usage_metadata.get('output_tokens', 0),
                    "total_tokens": result.usage_metadata.get('total_tokens', 0)
                }
            elif hasattr(result, 'response_metadata') and result.response_metadata:
                usage = result.response_metadata.get('token_usage', {})
                return {
                    "prompt_tokens": usage.get('prompt_tokens', 0),
                    "completion_tokens": usage.get('completion_tokens', 0),
                    "total_tokens": usage.get('total_tokens', 0)
                }
        except Exception as e:
            print(f"⚠️ 提取 Token 使用信息失败: {e}")
        
        return None
    
    def get_model_health_status(self) -> Dict[str, Any]:
        """获取模型健康状态"""
        return {
            "primary_model": {
                "name": LLM_CONFIG["model"],
                "base_url": LLM_CONFIG["base_url"],
                "status": "unknown"  # 需要实际测试
            },
            "secondary_model": {
                "name": LLM_CONFIG2["model"],
                "base_url": LLM_CONFIG2["base_url"],
                "status": "unknown"  # 需要实际测试
            }
        }


# 全局 LLM 降级处理器实例
llm_fallback_handler = LLMFallbackHandler()


def get_llm_fallback_handler() -> LLMFallbackHandler:
    """获取全局 LLM 降级处理器"""
    return llm_fallback_handler










