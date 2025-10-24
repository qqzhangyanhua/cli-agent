"""
输入处理模块
将复杂的输入处理逻辑拆分为多个单一职责的函数
"""

import sys
import logging
from typing import Optional

# 尝试导入智能文件输入（IDE 风格）
try:
    from src.ui.smart_file_input import (
        get_smart_input,
        check_prompt_toolkit_available,
    )
    USE_SMART_INPUT = True
except ImportError:
    USE_SMART_INPUT = False

from src.ui.interactive_file_selector import (
    interactive_file_select,
    quick_file_select,
)

logger = logging.getLogger(__name__)


def smart_input_handler(prompt: str = "👤 你: ") -> str:
    """
    智能输入处理器主入口

    职责：路由到智能输入或传统输入

    Args:
        prompt: 提示符

    Returns:
        用户输入的完整内容
    """
    # 尝试使用智能输入
    if USE_SMART_INPUT:
        smart_result = _try_smart_input(prompt)
        if smart_result is not None:
            return smart_result

    # 降级到传统输入
    return _traditional_input_loop(prompt)


def _try_smart_input(prompt: str) -> Optional[str]:
    """
    尝试使用智能输入模式

    Args:
        prompt: 提示符

    Returns:
        成功返回输入内容，失败返回 None

    Raises:
        KeyboardInterrupt, EOFError: 用户中断信号（不捕获）
    """
    if not check_prompt_toolkit_available():
        return None

    try:
        return get_smart_input(prompt)
    except (KeyboardInterrupt, EOFError):
        # 不捕获用户信号，向上传播
        raise
    except ImportError as e:
        logger.debug(f"Smart input unavailable: {e}")
        return None
    except Exception as e:
        logger.warning(f"Smart input failed: {e}, falling back to traditional mode")
        return None


def _traditional_input_loop(prompt: str) -> str:
    """
    传统输入模式循环

    Args:
        prompt: 提示符

    Returns:
        用户输入的完整内容
    """
    while True:
        try:
            user_input = input(prompt).strip()

            # 处理文件引用
            if user_input.startswith("@"):
                result = _handle_file_reference(user_input, prompt)
                if result is not None:
                    return result
                # result 为 None 表示需要重新输入
                continue

            # 普通输入，直接返回
            return user_input

        except (KeyboardInterrupt, EOFError):
            # 不直接退出，而是重新抛出异常让上层处理
            raise


def _handle_file_reference(user_input: str, prompt: str) -> Optional[str]:
    """
    处理文件引用输入（@ 开头）

    职责：
    1. 只输入 @ -> 交互式选择文件
    2. @filename -> 快速选择文件
    3. @filename operation -> 直接返回

    Args:
        user_input: 原始输入（以 @ 开头）
        prompt: 提示符

    Returns:
        完整的命令字符串，或 None（需要重新输入）
    """
    # 情况1: 只输入了 @
    if user_input == "@":
        return _interactive_file_selection(prompt)

    # 情况2: @filename 或 @filename operation
    parts = user_input.split(maxsplit=1)
    filename = parts[0][1:]  # 去掉 @

    # 如果已经有操作，直接返回
    if len(parts) == 2:
        return user_input

    # 没有操作，需要补全
    return _complete_file_operation(filename, prompt)


def _interactive_file_selection(prompt: str) -> Optional[str]:
    """
    交互式文件选择（用户只输入了 @）

    Args:
        prompt: 提示符

    Returns:
        完整命令或 None（取消选择）
    """
    print("\n🎯 启动文件选择器...")
    selected_file = interactive_file_select("选择要引用的文件")

    if not selected_file:
        print("🔄 继续输入...")
        return None

    # 选择了文件，提示用户输入操作
    print(f"\n✅ 已选择文件: @{selected_file}")
    new_prompt = f"👤 你 (已选择 @{selected_file}): "
    additional_input = input(new_prompt).strip()

    if additional_input:
        return f"@{selected_file} {additional_input}"
    else:
        return f"读取 @{selected_file}"


def _complete_file_operation(filename: str, prompt: str) -> Optional[str]:
    """
    补全文件操作（用户输入了 @filename 但没有操作）

    Args:
        filename: 文件名
        prompt: 提示符

    Returns:
        完整命令或 None（取消）
    """
    # 如果文件名较短，提供快速选择
    if len(filename) <= 10 and not any(c in filename for c in "./\\"):
        return _quick_file_selection(filename, prompt)

    # 文件名较长，直接提示输入操作
    return _prompt_for_operation(filename, prompt)


def _quick_file_selection(search_term: str, prompt: str) -> Optional[str]:
    """
    快速文件选择（搜索匹配）

    Args:
        search_term: 搜索关键词
        prompt: 提示符

    Returns:
        完整命令或 None
    """
    print(f"\n🔍 搜索文件: '{search_term}'...")
    selected_file = quick_file_select(search_term)

    if not selected_file:
        print("🔄 继续输入...")
        return None

    # 选择了文件，提示用户输入操作
    print(f"\n✅ 已选择: @{selected_file}")
    print("💡 请继续输入操作，例如: 总结内容、翻译、有哪些配置项\n")

    new_input = input(prompt).strip()

    if not new_input:
        return None

    # 用户重新输入了完整命令
    if new_input.startswith("@"):
        return new_input

    # 用户只输入了操作，补全文件名
    return f"@{selected_file} {new_input}"


def _prompt_for_operation(filename: str, prompt: str) -> Optional[str]:
    """
    提示用户输入操作

    Args:
        filename: 文件名
        prompt: 提��符

    Returns:
        完整命令或 None
    """
    print(f"\n✅ 检测到文件: @{filename}")
    print("💡 请继续输入操作，例如: 总结内容、翻译、有哪些配置项\n")

    new_input = input(prompt).strip()

    if not new_input:
        return None

    # 用户重新输入了完整命令
    if new_input.startswith("@"):
        return new_input

    # 用户只输入了操作，补全文件名
    return f"@{filename} {new_input}"
