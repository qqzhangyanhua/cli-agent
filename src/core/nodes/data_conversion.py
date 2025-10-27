"""
数据转换处理节点
支持 JSON/CSV/YAML 等格式之间的转换、验证和美化
"""

import json
from langchain_core.messages import HumanMessage

from src.core.agent_config import AgentState
from src.core.agent_llm import llm
from src.core.json_utils import extract_json_str, safe_json_loads
from src.tools.data_converter_tools import data_converter_tools


def data_conversion_processor(state: AgentState) -> dict:
    """
    数据转换处理节点
    支持 JSON/CSV/YAML 等格式之间的转换、验证和美化
    """
    user_input = state["user_input"]
    file_contents = state.get("file_contents", {})

    print(f"\n[数据转换] 处理请求...")

    # 使用 LLM 分析用户意图
    file_info = ""
    if file_contents:
        file_paths = list(file_contents.keys())
        file_info = f"\n\n📁 用户引用的文件:\n{chr(10).join(['- ' + p for p in file_paths])}"

    prompt = f"""分析用户的数据转换请求，返回JSON格式。

用户请求: {user_input}{file_info}

支持的操作类型:
1. convert: 格式转换 (json↔csv, json↔yaml, yaml↔json, xml→json)
2. validate: 格式验证
3. beautify: 格式美化

支持的格式: json, yaml, csv, xml

返回JSON:
{{
  "operation": "convert/validate/beautify",
  "source_format": "源格式或auto",
  "target_format": "目标格式(仅convert需要)",
  "file_path": "要处理的文件路径(如果用户引用了文件)"
}}

示例:
\"转换为CSV\" -> {{"operation": "convert", "source_format": "auto", "target_format": "csv"}}
\"验证JSON\" -> {{"operation": "validate", "source_format": "json"}}
\"美化JSON\" -> {{"operation": "beautify", "source_format": "json"}}

只返回JSON:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    response_text = result.content.strip()

    # 提取JSON
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    try:
        response_text = extract_json_str(response_text)
        parsed_obj, err = safe_json_loads(response_text)
        if err:
            raise json.JSONDecodeError(err, response_text, 0)
        parsed = parsed_obj
        operation = parsed.get("operation", "convert")
        source_format = parsed.get("source_format", "auto")
        target_format = parsed.get("target_format", "json")
        file_path = parsed.get("file_path", "")

        print(f"[数据转换] 操作:{operation} 源格式:{source_format} 目标格式:{target_format}")

        # 获取文件内容
        content = ""
        if file_path and file_path in file_contents:
            content = file_contents[file_path]
        elif file_contents:
            # 使用第一个文件
            content = list(file_contents.values())[0]
            file_path = list(file_contents.keys())[0]
        else:
            return {
                "response": "❌ 数据转换失败：未找到要处理的文件\n\n请使用 @ 引用要转换的文件，例如: @data.json 转换为CSV",
                "error": "No file content"
            }

        # 执行操作
        response = ""

        if operation == "convert":
            # 格式转换
            result = data_converter_tools.convert(
                content=content,
                source_format=source_format,
                target_format=target_format,
                file_path=file_path
            )

            if result["success"]:
                converted_content = result["result"]
                detected_format = result.get("source_format", source_format)

                response = f"✅ 数据转换成功\n\n"
                response += f"📄 源文件: {file_path}\n"
                response += f"📊 格式: {detected_format} → {target_format}\n"
                response += f"📏 大小: {len(content)} → {result['size']} 字符\n\n"
                response += f"转换结果:\n"
                response += "─" * 80 + "\n"

                # 限制输出长度
                if len(converted_content) > 2000:
                    response += converted_content[:2000] + "\n\n... (结果太长，已截断)\n"
                else:
                    response += converted_content + "\n"

                response += "─" * 80 + "\n\n"
                response += f"💡 提示: 可以将结果保存到文件"

                return {
                    "response": response,
                    "conversion_result": converted_content,
                    "source_format": detected_format,
                    "target_format": target_format
                }
            else:
                return {
                    "response": f"❌ 数据转换失败\n\n错误: {result['error']}",
                    "error": result["error"]
                }

        elif operation == "validate":
            # 格式验证
            result = data_converter_tools.validate(content, source_format)

            if result["success"]:
                response = f"🔍 数据验证结果\n\n"
                response += f"📄 文件: {file_path}\n"
                response += f"📊 格式: {source_format}\n"
                response += f"🎯 结果: {result['message']}\n"

                if not result["valid"]:
                    response += f"\n💡 提示: 请检查文件格式是否正确"

                return {"response": response}
            else:
                return {
                    "response": f"❌ 验证失败\n\n错误: {result['message']}",
                    "error": result["message"]
                }

        elif operation == "beautify":
            # 格式美化
            result = data_converter_tools.beautify(content, source_format)

            if result["success"]:
                beautified_content = result["result"]

                response = f"✨ 格式美化完成\n\n"
                response += f"📄 文件: {file_path}\n"
                response += f"📊 格式: {source_format}\n"
                response += f"📏 大小: {result['original_size']} → {result['formatted_size']} 字符\n\n"
                response += f"美化结果:\n"
                response += "─" * 80 + "\n"

                if len(beautified_content) > 2000:
                    response += beautified_content[:2000] + "\n\n... (结果太长，已截断)\n"
                else:
                    response += beautified_content + "\n"

                response += "─" * 80

                return {
                    "response": response,
                    "conversion_result": beautified_content
                }
            else:
                return {
                    "response": f"❌ 美化失败\n\n错误: {result['error']}",
                    "error": result["error"]
                }

    except json.JSONDecodeError as e:
        print(f"[数据转换] JSON解析失败: {e}")
        return {
            "response": "❌ 解析转换请求失败，请重试。\n\n示例：@data.json 转换为CSV",
            "error": str(e)
        }
    except Exception as e:
        print(f"[数据转换] 错误: {e}")
        return {
            "response": f"❌ 数据转换出错: {str(e)}",
            "error": str(e)
        }
