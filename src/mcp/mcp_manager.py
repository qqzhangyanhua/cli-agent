"""
MCP客户端管理器
用于管理和调用MCP服务器（包括desktop-commander）
"""

import subprocess
import json
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta
from src.mcp.mcp_filesystem import fs_tools


class MCPManager:
    """MCP服务器管理器 - 统一的工具注册表架构 + 缓存优化"""

    # 缓存文件路径
    CACHE_FILE = ".mcp_tools_cache.json"
    # 缓存有效期（小时）
    CACHE_TTL_HOURS = 24

    def __init__(self, config_path: Optional[str] = "mcp_config.json"):
        self.servers = {}
        self.tool_registry = {}  # 统一的工具注册表（核心数据结构）
        self.config = {}
        self._discovery_lock = threading.Lock()

        # 注册内置文件系统工具
        self._register_filesystem_tools()

        # 注册 LangChain 工具（待办、Git等）
        self._register_langchain_tools()

        # 加载MCP配置
        if config_path and Path(config_path).exists():
            self.load_config(config_path)

            # 先加载缓存（立即返回）
            self._load_tools_from_cache()

            # 后台异步刷新工具列表
            threading.Thread(
                target=self._discover_all_mcp_tools_async,
                daemon=True,
                name="MCP-Tool-Discovery"
            ).start()

    def load_config(self, config_path: str):
        """从JSON文件加载MCP配置"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            print(f"✅ 已加载MCP配置: {config_path}")

            if "mcpServers" in self.config:
                for name, server_config in self.config["mcpServers"].items():
                    self.servers[name] = server_config
                    print(f"   📡 注册服务器: {name}")

        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}")

    def _register_filesystem_tools(self):
        """注册内置文件系统工具"""
        self.tool_registry["fs_read"] = {
            "type": "builtin",
            "func": fs_tools.read_file,
            "description": "读取文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "max_lines": {"type": "integer", "description": "最大读取行数"}
                },
                "required": ["file_path"]
            }
        }

        self.tool_registry["fs_write"] = {
            "type": "builtin",
            "func": fs_tools.write_file,
            "description": "写入文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                    "mode": {"type": "string", "description": "写入模式(write/append)"}
                },
                "required": ["file_path", "content"]
            }
        }

        self.tool_registry["fs_list"] = {
            "type": "builtin",
            "func": fs_tools.list_directory,
            "description": "列出目录内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "目录路径"},
                    "pattern": {"type": "string", "description": "文件匹配模式"},
                    "recursive": {"type": "boolean", "description": "是否递归"}
                },
                "required": ["dir_path"]
            }
        }

        self.tool_registry["fs_search"] = {
            "type": "builtin",
            "func": fs_tools.search_files,
            "description": "搜索文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "搜索目录"},
                    "filename_pattern": {"type": "string", "description": "文件名模式"},
                    "content_search": {"type": "string", "description": "内容搜索"}
                },
                "required": ["dir_path"]
            }
        }

        self.tool_registry["fs_info"] = {
            "type": "builtin",
            "func": fs_tools.get_file_info,
            "description": "获取文件信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"}
                },
                "required": ["file_path"]
            }
        }

    def _register_langchain_tools(self):
        """注册 LangChain 工具（待办、Git等）"""
        # 待办工具
        self.tool_registry["add_todo"] = {
            "type": "langchain",
            "description": "添加待办事项。当用户想要记录、添加、设置待办或提醒时使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "日期（YYYY-MM-DD格式）"},
                    "time": {"type": "string", "description": "时间（HH:MM格式，可选）"},
                    "content": {"type": "string", "description": "待办内容"}
                },
                "required": ["date", "content"]
            }
        }

        self.tool_registry["query_todo"] = {
            "type": "langchain",
            "description": "查询待办事项。适用场景：'今天有什么要做的'、'查看明天的待办'、'搜索XX相关的待办'",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "查询类型：today(今天)、date(特定日期)、range(日期范围)、search(关键词搜索)"
                    },
                    "date": {"type": "string", "description": "特定日期（type=date时需要）"},
                    "start_date": {"type": "string", "description": "开始日期（type=range时需要）"},
                    "end_date": {"type": "string", "description": "结束日期（type=range时需要）"},
                    "keyword": {"type": "string", "description": "搜索关键词（type=search时需要）"}
                },
                "required": ["type"]
            }
        }

        # Git 工具
        self.tool_registry["generate_commit"] = {
            "type": "langchain",
            "description": "生成Git commit消息（仅生成，不提交）。适用场景：'生成commit日志'、'帮我写commit message'",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }

        self.tool_registry["auto_commit"] = {
            "type": "langchain",
            "description": "自动执行Git提交流程（git add -> 生成消息 -> git commit）。适用场景：'提交代码'、'一键提交'",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }

        self.tool_registry["git_pull"] = {
            "type": "langchain",
            "description": "拉取远程代码。适用场景：'拉取代码'、'git pull'、'更新代码'",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }

        self.tool_registry["git_push"] = {
            "type": "langchain",
            "description": "推送到远程仓库。适用场景：'推送代码'、'git push'、'上传代码'",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }

        self.tool_registry["code_review"] = {
            "type": "langchain",
            "description": "代码审查。适用场景：'code review'、'检查代码'、'审查代码'",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }

    def _load_tools_from_cache(self):
        """从缓存加载MCP工具列表（立即返回，无阻塞）"""
        if not Path(self.CACHE_FILE).exists():
            print("[MCP缓存] 缓存文件不存在，将进行首次发现")
            return

        try:
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 检查缓存有效期
            cache_time = datetime.fromisoformat(cache_data.get("timestamp", "1970-01-01T00:00:00"))
            if datetime.now() - cache_time > timedelta(hours=self.CACHE_TTL_HOURS):
                print(f"[MCP缓存] 缓存已过期（{self.CACHE_TTL_HOURS}小时），将刷新")
                return

            # 加载缓存的工具
            cached_tools = cache_data.get("tools", {})
            loaded_count = 0

            for server_name, server_tools in cached_tools.items():
                if server_name not in self.servers:
                    continue  # 服务器配置已删除

                for tool_name, tool_info in server_tools.items():
                    self.tool_registry[tool_name] = tool_info
                    loaded_count += 1

            if loaded_count > 0:
                print(f"[MCP缓存] ✅ 已从缓存加载 {loaded_count} 个MCP工具")
            else:
                print("[MCP缓存] 缓存为空")

        except Exception as e:
            print(f"[MCP缓存] ⚠️ 加载缓存失败: {e}")

    def _save_tools_to_cache(self):
        """保存MCP工具列表到缓存"""
        try:
            # 提取所有MCP工具
            mcp_tools_by_server = {}
            for tool_name, tool_info in self.tool_registry.items():
                if tool_info.get("type") == "mcp":
                    server_name = tool_info.get("server")
                    if server_name not in mcp_tools_by_server:
                        mcp_tools_by_server[server_name] = {}
                    mcp_tools_by_server[server_name][tool_name] = tool_info

            # 构建缓存数据
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "tools": mcp_tools_by_server
            }

            # 写入缓存文件
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)


        except Exception as e:
            print(f"[MCP缓存] ⚠️ 保存缓存失败: {e}")

    def _discover_all_mcp_tools_async(self):
        """异步发现所有MCP工具（后台线程）"""
        time.sleep(0.5)  # 让主程序先启动

        with self._discovery_lock:
            self._discover_all_mcp_tools_parallel()
            self._save_tools_to_cache()

    def _discover_all_mcp_tools_parallel(self):
        """并行发现所有MCP服务器的工具（优化版）"""
        if not self.servers:
            return

        discovered_count = 0

        # 使用线程池并行查询多个服务器
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有发现任务
            future_to_server = {
                executor.submit(self._discover_tools_from_server, server_name): server_name
                for server_name in self.servers
            }

            # 收集结果（总超时5秒）
            for future in as_completed(future_to_server, timeout=5):
                server_name = future_to_server[future]
                try:
                    count = future.result(timeout=3)  # 单个服务器最多3秒
                    discovered_count += count
                except FutureTimeoutError:
                    print(f"[MCP发现] ⏱️ {server_name} 超时(>3秒)，跳过")
                except Exception as e:
                    print(f"[MCP发现] ⚠️ {server_name} 发现失败: {e}")

     

    def _discover_tools_from_server(self, server_name: str) -> int:
        """
        从单个MCP服务器发现工具

        Args:
            server_name: 服务器名称

        Returns:
            发现的工具数量
        """
        try:
            tools = self._list_tools_from_server(server_name)

            if not tools:
                return 0

            count = 0
            for tool in tools:
                tool_name = tool.get("name", "")
                if not tool_name:
                    continue

                # 注册到工具注册表
                self.tool_registry[tool_name] = {
                    "type": "mcp",
                    "server": server_name,
                    "method": tool_name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
                count += 1

            return count

        except Exception as e:
            print(f"   ⚠️ 无法从 {server_name} 发现工具: {e}")
            return 0

    def _list_tools_from_server(self, server_name: str) -> List[Dict]:
        """
        调用MCP服务器的tools/list获取工具列表

        Args:
            server_name: 服务器名称

        Returns:
            工具列表
        """
        if server_name not in self.servers:
            return []

        server_config = self.servers[server_name]

        try:
            # 构建命令
            command = [server_config["command"]] + server_config["args"]

            # 构建MCP请求（tools/list）
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }

            # 使用 Popen 进行交互式通信
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # 发送请求并获取响应（优化：3秒超时）
            stdout, stderr = process.communicate(
                input=json.dumps(request) + "\n", timeout=3
            )

            if process.returncode == 0:
                # 解析响应
                stdout_lines = stdout.strip().split("\n")
                json_response = None

                # 查找 JSON 响应行
                for line in reversed(stdout_lines):
                    line = line.strip()
                    if line and (line.startswith("{") or line.startswith("[")):
                        try:
                            json_response = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue

                if not json_response:
                    json_response = json.loads(stdout)

                # 提取工具列表
                result = json_response.get("result", {})
                tools = result.get("tools", [])

                return tools
            else:
                print(f"      错误输出: {stderr}")
                return []

        except subprocess.TimeoutExpired:
            print(f"      超时(>10秒)")
            return []
        except Exception as e:
            print(f"      异常: {str(e)}")
            return []

    def call_mcp_server(
        self, server_name: str, tool_name: str, params: Dict = None
    ) -> Dict:
        """
        调用MCP服务器工具

        Args:
            server_name: 服务器名称（如 "desktop-commander"）
            tool_name: 工具名称
            params: 工具参数

        Returns:
            {"success": bool, "result": Any, "error": str}
        """
        if server_name not in self.servers:
            return {"success": False, "error": f"MCP服务器未配置: {server_name}"}

        server_config = self.servers[server_name]

        try:
            # 构建命令
            command = [server_config["command"]] + server_config["args"]

            # 构建MCP请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": params or {}},
            }

            print(f"[MCP调用] 服务器: {server_name}, 工具: {tool_name}")

            # 使用 Popen 进行交互式通信
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # 发送请求并获取响应
            stdout, stderr = process.communicate(
                input=json.dumps(request) + "\n", timeout=30
            )

            # 创建一个类似 subprocess.run 结果的对象
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            result = Result(process.returncode, stdout, stderr)

            if result.returncode == 0:
                try:
                    # 尝试解析标准输出中的 JSON
                    stdout_lines = result.stdout.strip().split("\n")
                    json_response = None

                    # 查找 JSON 响应行（通常是最后一行或包含 "jsonrpc" 的行）
                    for line in reversed(stdout_lines):
                        line = line.strip()
                        if line and (line.startswith("{") or line.startswith("[")):
                            try:
                                json_response = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue

                    if not json_response:
                        # 如果没找到 JSON，尝试解析整个输出
                        json_response = json.loads(result.stdout)

                    print(f"[MCP调用] ✅ 成功")

                    # 解析 MCP 标准格式的结果
                    result_data = json_response.get("result", {})
                    if isinstance(result_data, dict) and "content" in result_data:
                        # 提取 content 数组中的文本内容
                        content_items = result_data.get("content", [])
                        if content_items and isinstance(content_items, list):
                            # 合并所有文本内容
                            text_content = ""
                            for item in content_items:
                                if (
                                    isinstance(item, dict)
                                    and item.get("type") == "text"
                                ):
                                    text_content += item.get("text", "")

                            return {
                                "success": True,
                                "result": text_content.strip(),
                                "raw_response": json_response,
                            }

                    # 如果不是标准格式，返回原始结果
                    return {
                        "success": True,
                        "result": result_data,
                        "raw_response": json_response,
                    }
                except json.JSONDecodeError as e:
                    print(f"[MCP调用] JSON解析失败: {e}")
                    print(f"[MCP调用] 原始输出: {result.stdout}")
                    return {
                        "success": True,
                        "result": result.stdout,
                        "output": result.stdout,
                    }
            else:
                print(f"[MCP调用] ❌ 失败: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "命令执行失败",
                    "stdout": result.stdout,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "⏱️ 命令执行超时(>30秒)"}
        except Exception as e:
            return {"success": False, "error": f"❌ 调用失败: {str(e)}"}

    def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        统一的工具调用接口 - 零分支自动分发

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        # 检查工具是否存在
        if tool_name not in self.tool_registry:
            return {"success": False, "error": f"未知的工具: {tool_name}"}

        tool = self.tool_registry[tool_name]

        try:
            if tool["type"] == "builtin":
                # 内置工具：直接调用函数
                func = tool["func"]

                # 过滤参数（只传递函数需要的参数）
                func_params = {
                    k: v for k, v in kwargs.items()
                    if k in tool["parameters"].get("properties", {}) and v is not None
                }

                result = func(**func_params)
                return result

            elif tool["type"] == "mcp":
                # MCP工具：调用服务器
                return self.call_mcp_server(
                    server_name=tool["server"],
                    tool_name=tool["method"],
                    params=kwargs
                )

            else:
                return {"success": False, "error": f"未知的工具类型: {tool['type']}"}

        except Exception as e:
            return {"success": False, "error": f"工具执行失败: {str(e)}"}

    def list_available_tools(self) -> List[Dict]:
        """动态生成工具列表 - 零硬编码"""
        return [
            {
                "name": name,
                "description": tool["description"],
                "type": tool["type"],
                "parameters": tool["parameters"]
            }
            for name, tool in self.tool_registry.items()
        ]


# ============================================
# 全局实例
# ============================================

mcp_manager = MCPManager("mcp_config.json")


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("🔧 MCP管理器测试")
    print("=" * 80)

    # 测试文件系统工具
    print("\n📁 测试1: 文件系统工具")
    print("-" * 80)

    result = mcp_manager.call_tool("fs_list", dir_path=".", pattern="*.py")
    if result["success"]:
        print(f"✅ 找到 {result['total_files']} 个Python文件")
        for f in result["files"][:3]:
            print(f"   - {f['name']} ({f['size_human']})")

    # 列出所有可用工具
    print("\n\n🛠️ 测试2: 可用工具列表")
    print("-" * 80)
    tools = mcp_manager.list_available_tools()

    fs_tools_list = [t for t in tools if t["type"] == "filesystem"]
    builtin_tools = [t for t in tools if t["type"] == "builtin"]
    mcp_tools = [t for t in tools if t["type"] == "mcp"]

    print(f"\n📁 内置工具 ({len(builtin_tools)}个):")
    for tool in builtin_tools:
        print(f"   • {tool['name']:15} - {tool['description']}")

    if mcp_tools:
        print(f"\n🔌 MCP工具 ({len(mcp_tools)}个):")
        for tool in mcp_tools:
            print(f"   • {tool['name']:25} - {tool['description']}")

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("\n💡 提示: 使用 mcp_manager.call_tool(tool_name, **params) 调用工具")
