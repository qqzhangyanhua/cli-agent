"""
MCP文件系统工具模块
提供安全的文件系统访问功能

使用: from mcp_filesystem import FileSystemTools, fs_tools
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class FileSystemTools:
    """文件系统访问工具（MCP-like实现）"""
    
    def __init__(self, allowed_dirs: List[str], max_file_size: int = 10*1024*1024, 
                 allowed_extensions: List[str] = None):
        """
        初始化文件系统工具
        
        Args:
            allowed_dirs: 允许访问的目录列表
            max_file_size: 最大文件大小（字节）
            allowed_extensions: 允许的文件扩展名列表
        """
        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs]
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or [
            ".txt", ".py", ".json", ".csv", ".md", ".log", ".sh", ".yml", ".yaml"
        ]
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """检查路径是否在允许的目录内"""
        try:
            path = Path(file_path).resolve()
            return any(path.is_relative_to(allowed_dir) or str(path).startswith(str(allowed_dir))
                      for allowed_dir in self.allowed_dirs)
        except Exception:
            return False
    
    def _check_file_size(self, file_path: str) -> bool:
        """检查文件大小"""
        try:
            return os.path.getsize(file_path) <= self.max_file_size
        except Exception:
            return False
    
    def _check_extension(self, file_path: str) -> bool:
        """检查文件扩展名"""
        ext = Path(file_path).suffix.lower()
        return ext in self.allowed_extensions or ext == ""
    
    def read_file(self, file_path: str, max_lines: Optional[int] = None) -> Dict:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            max_lines: 最大读取行数（None表示全部读取）
        
        Returns:
            {
                "success": bool,
                "content": str,
                "size": int,
                "lines": int,
                "error": str (if failed)
            }
        """
        try:
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"⛔ 拒绝访问: 路径不在允许的目录内"
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"📂 文件不存在: {file_path}"
                }
            
            if not self._check_file_size(file_path):
                return {
                    "success": False,
                    "error": f"📦 文件太大（超过{self.max_file_size // 1024 // 1024}MB）"
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line)
                    content = ''.join(lines)
                    truncated = True
                else:
                    content = f.read()
                    truncated = False
            
            result = {
                "success": True,
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1,
                "path": file_path
            }
            
            if truncated:
                result["truncated"] = True
                result["max_lines"] = max_lines
            
            return result
        
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "🔒 无法读取文件（可能是二进制文件）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 读取失败: {str(e)}"
            }
    
    def write_file(self, file_path: str, content: str, mode: str = "w") -> Dict:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            mode: 写入模式 ('w'=覆盖, 'a'=追加)
        
        Returns:
            {
                "success": bool,
                "path": str,
                "size": int,
                "lines": int,
                "error": str (if failed)
            }
        """
        try:
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"⛔ 拒绝访问: 路径不在允许的目录内"
                }
            
            if not self._check_extension(file_path):
                return {
                    "success": False,
                    "error": f"🚫 不允许的文件类型（允许: {', '.join(self.allowed_extensions)}）"
                }
            
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": file_path,
                "size": len(content),
                "lines": content.count('\n') + 1,
                "mode": "覆盖" if mode == "w" else "追加"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 写入失败: {str(e)}"
            }
    
    def list_directory(self, dir_path: str, pattern: str = "*", recursive: bool = False) -> Dict:
        """
        列出目录内容
        
        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式 (*, *.py等)
            recursive: 是否递归列出子目录
        
        Returns:
            {
                "success": bool,
                "path": str,
                "files": List[Dict],
                "directories": List[Dict],
                "total_files": int,
                "total_dirs": int,
                "error": str (if failed)
            }
        """
        try:
            if not self._is_path_allowed(dir_path):
                return {
                    "success": False,
                    "error": f"⛔ 拒绝访问: 路径不在允许的目录内"
                }
            
            if not os.path.exists(dir_path):
                return {
                    "success": False,
                    "error": f"📂 目录不存在: {dir_path}"
                }
            
            if not os.path.isdir(dir_path):
                return {
                    "success": False,
                    "error": f"⚠️  不是目录: {dir_path}"
                }
            
            path = Path(dir_path)
            files = []
            dirs = []
            
            # 选择glob或rglob
            glob_method = path.rglob if recursive else path.glob
            
            for item in glob_method(pattern):
                if not self._is_path_allowed(str(item)):
                    continue
                    
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "size_human": self._human_readable_size(item.stat().st_size),
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "extension": item.suffix
                    })
                elif item.is_dir():
                    dirs.append({
                        "name": item.name,
                        "path": str(item)
                    })
            
            # 排序
            files.sort(key=lambda x: x['name'])
            dirs.sort(key=lambda x: x['name'])
            
            return {
                "success": True,
                "path": dir_path,
                "files": files,
                "directories": dirs,
                "total_files": len(files),
                "total_dirs": len(dirs),
                "pattern": pattern,
                "recursive": recursive
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 列出目录失败: {str(e)}"
            }
    
    def search_files(self, dir_path: str, filename_pattern: str = "*", 
                    content_search: Optional[str] = None, max_results: int = 50) -> Dict:
        """
        搜索文件
        
        Args:
            dir_path: 搜索的目录路径
            filename_pattern: 文件名匹配模式
            content_search: 内容搜索关键词（可选）
            max_results: 最大返回结果数
        
        Returns:
            {
                "success": bool,
                "matches": List[Dict],
                "total": int,
                "truncated": bool,
                "error": str (if failed)
            }
        """
        try:
            if not self._is_path_allowed(dir_path):
                return {
                    "success": False,
                    "error": f"⛔ 拒绝访问: 路径不在允许的目录内"
                }
            
            path = Path(dir_path)
            matches = []
            
            for item in path.rglob(filename_pattern):
                if len(matches) >= max_results:
                    break
                    
                if not item.is_file() or not self._is_path_allowed(str(item)):
                    continue
                
                match_info = {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "size_human": self._human_readable_size(item.stat().st_size),
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 如果需要内容搜索
                if content_search and self._check_extension(str(item)) and self._check_file_size(str(item)):
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content_search.lower() in content.lower():
                                # 找到匹配的行
                                lines = content.split('\n')
                                matched_lines = [
                                    (i+1, line) for i, line in enumerate(lines) 
                                    if content_search.lower() in line.lower()
                                ]
                                match_info["content_matched"] = True
                                match_info["matched_lines"] = matched_lines[:5]  # 最多显示5行
                                matches.append(match_info)
                    except:
                        pass
                else:
                    matches.append(match_info)
            
            return {
                "success": True,
                "matches": matches,
                "total": len(matches),
                "truncated": len(matches) >= max_results,
                "max_results": max_results,
                "search_pattern": filename_pattern,
                "content_search": content_search
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 搜索失败: {str(e)}"
            }
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        获取文件信息
        
        Returns:
            {
                "success": bool,
                "name": str,
                "path": str,
                "size": int,
                "modified": str,
                "created": str,
                "is_file": bool,
                "is_dir": bool,
                "extension": str,
                "error": str (if failed)
            }
        """
        try:
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"⛔ 拒绝访问: 路径不在允许的目录内"
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"📂 路径不存在: {file_path}"
                }
            
            path = Path(file_path)
            stat = path.stat()
            
            return {
                "success": True,
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "size_human": self._human_readable_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "extension": path.suffix if path.is_file() else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ 获取信息失败: {str(e)}"
            }
    
    def _human_readable_size(self, size: int) -> str:
        """转换文件大小为人类可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"


# ============================================
# 全局实例（可直接导入使用）
# ============================================

# 默认配置
DEFAULT_ALLOWED_DIRS = [
    "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example",
    "/Users/zhangyanhua/Desktop/AI/tushare/quantification"
]

fs_tools = FileSystemTools(
    allowed_dirs=DEFAULT_ALLOWED_DIRS,
    max_file_size=10 * 1024 * 1024,  # 10MB
    allowed_extensions=[".txt", ".py", ".json", ".csv", ".md", ".log", ".sh", ".yml", ".yaml"]
)


# ============================================
# 使用示例
# ============================================

if __name__ == "__main__":
    print("📁 MCP文件系统工具测试")
    print("=" * 60)
    
    # 测试读取文件
    print("\n1. 测试读取文件:")
    result = fs_tools.read_file("mcp_filesystem.py", max_lines=10)
    if result["success"]:
        print(f"✅ 成功读取 {result['lines']} 行")
    else:
        print(f"❌ {result['error']}")
    
    # 测试列出目录
    print("\n2. 测试列出目录:")
    result = fs_tools.list_directory(".", "*.py")
    if result["success"]:
        print(f"✅ 找到 {result['total_files']} 个Python文件")
        for f in result['files'][:5]:
            print(f"   - {f['name']} ({f['size_human']})")
    else:
        print(f"❌ {result['error']}")
    
    # 测试搜索
    print("\n3. 测试搜索文件:")
    result = fs_tools.search_files(".", "*.md")
    if result["success"]:
        print(f"✅ 找到 {result['total']} 个Markdown文件")
    else:
        print(f"❌ {result['error']}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
