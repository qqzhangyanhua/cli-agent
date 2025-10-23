"""
MCP客户端管理器
用于管理和调用MCP服务器（包括desktop-commander）
"""

import subprocess
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.mcp.mcp_filesystem import fs_tools


class MCPManager:
    """MCP服务器管理器"""
    
    def __init__(self, config_path: Optional[str] = "mcp_config.json"):
        self.servers = {}
        self.tools = {}
        self.config = {}
        
        # 注册内置文件系统工具
        self._register_filesystem_tools()
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """从JSON文件加载MCP配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
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
        self.tools["fs_read"] = {
            "name": "fs_read",
            "description": "读取文件内容",
            "params": ["file_path", "max_lines"],
            "func": fs_tools.read_file
        }
        
        self.tools["fs_write"] = {
            "name": "fs_write",
            "description": "写入文件内容",
            "params": ["file_path", "content", "mode"],
            "func": fs_tools.write_file
        }
        
        self.tools["fs_list"] = {
            "name": "fs_list",
            "description": "列出目录内容",
            "params": ["dir_path", "pattern", "recursive"],
            "func": fs_tools.list_directory
        }
        
        self.tools["fs_search"] = {
            "name": "fs_search",
            "description": "搜索文件",
            "params": ["dir_path", "filename_pattern", "content_search"],
            "func": fs_tools.search_files
        }
        
        self.tools["fs_info"] = {
            "name": "fs_info",
            "description": "获取文件信息",
            "params": ["file_path"],
            "func": fs_tools.get_file_info
        }
    
    def call_mcp_server(self, server_name: str, tool_name: str, params: Dict = None) -> Dict:
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
            return {
                "success": False,
                "error": f"MCP服务器未配置: {server_name}"
            }
        
        server_config = self.servers[server_name]
        
        try:
            # 构建命令
            command = [server_config["command"]] + server_config["args"]
            
            # 构建MCP请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params or {}
                }
            }
            
            print(f"[MCP调用] 服务器: {server_name}, 工具: {tool_name}")
            
            # 使用 Popen 进行交互式通信
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 发送请求并获取响应
            stdout, stderr = process.communicate(
                input=json.dumps(request) + '\n',
                timeout=30
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
                    stdout_lines = result.stdout.strip().split('\n')
                    json_response = None
                    
                    # 查找 JSON 响应行（通常是最后一行或包含 "jsonrpc" 的行）
                    for line in reversed(stdout_lines):
                        line = line.strip()
                        if line and (line.startswith('{') or line.startswith('[')):
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
                                if isinstance(item, dict) and item.get("type") == "text":
                                    text_content += item.get("text", "")
                            
                            return {
                                "success": True,
                                "result": text_content.strip(),
                                "raw_response": json_response
                            }
                    
                    # 如果不是标准格式，返回原始结果
                    return {
                        "success": True,
                        "result": result_data,
                        "raw_response": json_response
                    }
                except json.JSONDecodeError as e:
                    print(f"[MCP调用] JSON解析失败: {e}")
                    print(f"[MCP调用] 原始输出: {result.stdout}")
                    return {
                        "success": True,
                        "result": result.stdout,
                        "output": result.stdout
                    }
            else:
                print(f"[MCP调用] ❌ 失败: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "命令执行失败",
                    "stdout": result.stdout
                }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "⏱️ 命令执行超时(>30秒)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 调用失败: {str(e)}"
            }
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        统一的工具调用接口
        
        Args:
            tool_name: 工具名称（fs_read, desktop_commander, etc）
            **kwargs: 工具参数
        
        Returns:
            工具执行结果
        """
        # 内置文件系统工具
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            try:
                func_params = {k: v for k, v in kwargs.items() if k in tool["params"] and v is not None}
                result = tool["func"](**func_params)
                return result
            except Exception as e:
                return {
                    "success": False,
                    "error": f"工具执行失败: {str(e)}"
                }
        
        # desktop-commander工具
        elif tool_name.startswith("desktop_"):
            action = tool_name.replace("desktop_", "")
            return self.call_mcp_server("desktop-commander", action, kwargs)
        
        # mcp-stock工具
        elif tool_name == "get_stock_info":
            return self.call_mcp_server("mcp-stock", "get-stock-info", kwargs)
        
        else:
            return {
                "success": False,
                "error": f"未知的工具: {tool_name}"
            }
    
    def list_available_tools(self) -> List[Dict]:
        """列出所有可用的工具"""
        tools_list = []
        
        # 文件系统工具
        for name, tool in self.tools.items():
            tools_list.append({
                "name": name,
                "description": tool["description"],
                "type": "filesystem",
                "params": tool["params"]
            })
        
        # desktop-commander工具（如果已配置）
        if "desktop-commander" in self.servers:
            tools_list.extend([
                {
                    "name": "desktop_execute",
                    "description": "执行桌面命令或脚本",
                    "type": "desktop-commander",
                    "params": ["command", "args"]
                },
                {
                    "name": "desktop_screenshot",
                    "description": "截取屏幕截图",
                    "type": "desktop-commander",
                    "params": ["output_path"]
                },
                {
                    "name": "desktop_read_clipboard",
                    "description": "读取剪贴板内容",
                    "type": "desktop-commander",
                    "params": []
                },
                {
                    "name": "desktop_write_clipboard",
                    "description": "写入剪贴板内容",
                    "type": "desktop-commander",
                    "params": ["text"]
                }
            ])
        
        # mcp-stock工具（如果已配置）
        if "mcp-stock" in self.servers:
            tools_list.extend([
                {
                    "name": "get_stock_info",
                    "description": "获取股票实时信息",
                    "type": "mcp-stock",
                    "params": ["stock_code"]
                }
            ])
        
        return tools_list


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
        for f in result['files'][:3]:
            print(f"   - {f['name']} ({f['size_human']})")
    
    # 列出所有可用工具
    print("\n\n🛠️ 测试2: 可用工具列表")
    print("-" * 80)
    tools = mcp_manager.list_available_tools()
    
    fs_tools_list = [t for t in tools if t['type'] == 'filesystem']
    desktop_tools = [t for t in tools if t['type'] == 'desktop-commander']
    
    print(f"\n📁 文件系统工具 ({len(fs_tools_list)}个):")
    for tool in fs_tools_list:
        print(f"   • {tool['name']:15} - {tool['description']}")
    
    if desktop_tools:
        print(f"\n🖥️ 桌面控制工具 ({len(desktop_tools)}个):")
        for tool in desktop_tools:
            print(f"   • {tool['name']:25} - {tool['description']}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("\n💡 提示: 使用 mcp_manager.call_tool(tool_name, **params) 调用工具")
