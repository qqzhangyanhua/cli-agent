"""
交互式文件选择器模块
支持友好的文件选择界面和快捷操作
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import re


class InteractiveFileSelector:
    """交互式文件选择器"""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = Path(working_dir or os.getcwd())
        self.files_per_page = 15  # 每页显示的文件数
        self.current_page = 0
        self.filtered_files = []
        self.all_files = []
        
    def get_files_list(self, show_hidden: bool = False) -> List[dict]:
        """获取当前目录的文件列表"""
        files = []
        
        try:
            for item in sorted(self.working_dir.iterdir()):
                # 跳过隐藏文件（除非明确要求显示）
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                # 获取文件信息
                try:
                    stat = item.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime
                except (OSError, PermissionError):
                    size = 0
                    mtime = 0
                
                file_info = {
                    'name': item.name,
                    'path': str(item),
                    'is_dir': item.is_dir(),
                    'size': size,
                    'mtime': mtime,
                    'icon': self._get_file_icon(item)
                }
                files.append(file_info)
                
        except (PermissionError, OSError) as e:
            print(f"❌ 无法读取目录: {e}")
            
        return files
    
    def _get_file_icon(self, path: Path) -> str:
        """获取文件图标"""
        if path.is_dir():
            return "📁"
        
        suffix = path.suffix.lower()
        icon_map = {
            '.py': '🐍',
            '.js': '🟨', 
            '.ts': '🔷',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.zip': '📦', '.tar': '📦', '.gz': '📦',
            '.exe': '⚙️', '.app': '⚙️',
            '.sh': '🔧', '.bat': '🔧',
        }
        
        return icon_map.get(suffix, '📄')
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}K"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f}M"
        else:
            return f"{size/(1024*1024*1024):.1f}G"
    
    def filter_files(self, files: List[dict], filter_text: str) -> List[dict]:
        """根据输入文本过滤文件"""
        if not filter_text:
            return files
        
        filter_text = filter_text.lower()
        filtered = []
        
        for file in files:
            name_lower = file['name'].lower()
            
            # 精确匹配优先
            if name_lower == filter_text:
                filtered.insert(0, file)
            # 开头匹配
            elif name_lower.startswith(filter_text):
                filtered.append(file)
            # 包含匹配
            elif filter_text in name_lower:
                filtered.append(file)
        
        return filtered
    
    def display_files_page(self, files: List[dict], page: int = 0, filter_text: str = "") -> Tuple[int, int]:
        """显示文件列表页面"""
        start_idx = page * self.files_per_page
        end_idx = start_idx + self.files_per_page
        page_files = files[start_idx:end_idx]
        
        total_pages = (len(files) + self.files_per_page - 1) // self.files_per_page
        
        # 清屏并显示标题
        print("\033[2J\033[H", end="")  # 清屏
        print("📁 交互式文件选择器")
        print("=" * 60)
        print(f"📂 当前目录: {self.working_dir}")
        
        if filter_text:
            print(f"🔍 过滤条件: '{filter_text}' (找到 {len(files)} 个匹配)")
        
        print(f"📄 第 {page + 1}/{total_pages} 页 (共 {len(files)} 个文件)")
        print("-" * 60)
        
        # 显示文件列表
        if not page_files:
            print("📭 没有找到匹配的文件")
        else:
            for i, file in enumerate(page_files, 1):
                global_idx = start_idx + i
                icon = file['icon']
                name = file['name']
                
                # 文件大小和类型信息
                if file['is_dir']:
                    info = "目录"
                else:
                    info = self._format_size(file['size'])
                
                # 高亮显示匹配的部分
                if filter_text and filter_text in name.lower():
                    name = self._highlight_match(name, filter_text)
                
                print(f"  {global_idx:2d}. {icon} {name:<30} {info:>8}")
        
        print("-" * 60)
        print("💡 操作提示:")
        print("  • 输入数字选择文件")
        print("  • 输入文件名进行搜索")
        print("  • 'n' 下一页, 'p' 上一页")
        print("  • 'r' 刷新, 'h' 显示隐藏文件")
        print("  • 'q' 或 'exit' 退出选择")
        print("-" * 60)
        
        return len(page_files), total_pages
    
    def _highlight_match(self, text: str, pattern: str) -> str:
        """高亮显示匹配的文本"""
        # 简单的高亮实现，在终端中用颜色标记
        pattern_lower = pattern.lower()
        text_lower = text.lower()
        
        if pattern_lower in text_lower:
            start = text_lower.find(pattern_lower)
            end = start + len(pattern)
            return (text[:start] + 
                   f"\033[93m{text[start:end]}\033[0m" +  # 黄色高亮
                   text[end:])
        return text
    
    def select_file(self, prompt: str = "选择文件") -> Optional[str]:
        """启动交互式文件选择"""
        print(f"\n🎯 {prompt}")
        
        # 获取文件列表
        self.all_files = self.get_files_list()
        self.filtered_files = self.all_files
        self.current_page = 0
        show_hidden = False
        filter_text = ""
        
        while True:
            # 显示当前页
            page_count, total_pages = self.display_files_page(
                self.filtered_files, self.current_page, filter_text
            )
            
            # 获取用户输入
            try:
                user_input = input("\n👤 请选择 (输入数字/搜索/命令): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 已取消文件选择")
                return None
            
            if not user_input:
                continue
            
            # 处理退出命令
            if user_input.lower() in ['q', 'quit', 'exit', '退出']:
                print("\n👋 已取消文件选择")
                return None
            
            # 处理导航命令
            if user_input.lower() == 'n':  # 下一页
                if self.current_page < total_pages - 1:
                    self.current_page += 1
                continue
            
            if user_input.lower() == 'p':  # 上一页
                if self.current_page > 0:
                    self.current_page -= 1
                continue
            
            if user_input.lower() == 'r':  # 刷新
                self.all_files = self.get_files_list(show_hidden)
                self.filtered_files = self.filter_files(self.all_files, filter_text)
                self.current_page = 0
                continue
            
            if user_input.lower() == 'h':  # 显示/隐藏隐藏文件
                show_hidden = not show_hidden
                self.all_files = self.get_files_list(show_hidden)
                self.filtered_files = self.filter_files(self.all_files, filter_text)
                self.current_page = 0
                continue
            
            # 尝试解析为数字选择
            try:
                choice = int(user_input)
                if 1 <= choice <= len(self.filtered_files):
                    selected_file = self.filtered_files[choice - 1]
                    print(f"\n✅ 已选择: {selected_file['icon']} {selected_file['name']}")
                    return selected_file['name']
                else:
                    print(f"\n❌ 无效选择，请输入 1-{len(self.filtered_files)} 之间的数字")
                    input("按 Enter 继续...")
                    continue
            except ValueError:
                pass
            
            # 作为搜索文本处理
            filter_text = user_input
            self.filtered_files = self.filter_files(self.all_files, filter_text)
            self.current_page = 0
            
            # 如果只有一个匹配结果，询问是否直接选择
            if len(self.filtered_files) == 1:
                file = self.filtered_files[0]
                confirm = input(f"\n💡 找到唯一匹配: {file['icon']} {file['name']}，是否选择? (y/N): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    print(f"\n✅ 已选择: {file['icon']} {file['name']}")
                    return file['name']
    
    def quick_select_with_preview(self, partial_name: str = "") -> Optional[str]:
        """快速选择模式，显示匹配预览"""
        files = self.get_files_list()
        
        if partial_name:
            files = self.filter_files(files, partial_name)
        
        if not files:
            print(f"\n❌ 没有找到匹配 '{partial_name}' 的文件")
            return None
        
        if len(files) == 1:
            # 只有一个匹配，直接返回
            file = files[0]
            print(f"\n✅ 自动选择: {file['icon']} {file['name']}")
            return file['name']
        
        # 多个匹配，显示简化列表
        print(f"\n🔍 找到 {len(files)} 个匹配 '{partial_name}' 的文件:")
        print("-" * 50)
        
        for i, file in enumerate(files[:10], 1):  # 只显示前10个
            icon = file['icon']
            name = file['name']
            if partial_name:
                name = self._highlight_match(name, partial_name)
            print(f"  {i}. {icon} {name}")
        
        if len(files) > 10:
            print(f"  ... 还有 {len(files) - 10} 个文件")
        
        print("-" * 50)
        
        try:
            choice = input("👤 选择文件 (输入数字或按 Enter 进入完整选择器): ").strip()
            
            if not choice:
                # 进入完整选择器
                return self.select_file(f"选择匹配 '{partial_name}' 的文件")
            
            choice_num = int(choice)
            if 1 <= choice_num <= min(len(files), 10):
                selected_file = files[choice_num - 1]
                print(f"\n✅ 已选择: {selected_file['icon']} {selected_file['name']}")
                return selected_file['name']
            else:
                print(f"\n❌ 无效选择")
                return None
                
        except (ValueError, KeyboardInterrupt):
            print("\n👋 已取消选择")
            return None


# 全局选择器实例
file_selector = InteractiveFileSelector()


def update_selector_working_directory(new_dir: str):
    """更新选择器工作目录"""
    global file_selector
    file_selector.working_dir = Path(new_dir)


def interactive_file_select(prompt: str = "选择文件") -> Optional[str]:
    """交互式文件选择的便捷函数"""
    return file_selector.select_file(prompt)


def quick_file_select(partial_name: str = "") -> Optional[str]:
    """快速文件选择的便捷函数"""
    return file_selector.quick_select_with_preview(partial_name)
