"""
智能文件输入模块 - IDE 风格的 @ 文件引用
参考 Codex/Claude Code 的用户体验

特性:
- 实时自动补全 (输入 @ 后立即显示建议)
- 模糊搜索和过滤
- 上下箭头导航
- Tab 键补全
- 显示文件图标和相对路径
- 支持多文件引用
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False
    # 定义占位符类，避免导入错误
    Completer = object
    Completion = object
    Document = object


@dataclass
class FileItem:
    """文件项信息"""
    name: str
    path: str
    relative_path: str
    is_dir: bool
    icon: str
    size: int = 0


class FileCompleter(Completer if HAS_PROMPT_TOOLKIT else object):
    """文件自动补全器"""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = Path(working_dir or os.getcwd())
        self._file_cache: List[FileItem] = []
        self._cache_valid = False
        
    def _refresh_file_cache(self):
        """刷新文件缓存"""
        self._file_cache = []
        self._scan_directory(self.working_dir, depth=0, max_depth=3)
        self._cache_valid = True
    
    def _scan_directory(self, directory: Path, depth: int = 0, max_depth: int = 3):
        """递归扫描目录"""
        if depth > max_depth:
            return
        
        try:
            for item in sorted(directory.iterdir()):
                # 跳过隐藏文件和常见的忽略目录
                if item.name.startswith('.'):
                    continue
                if item.is_dir() and item.name in ['node_modules', '__pycache__', 'venv', '.git']:
                    continue
                
                # 计算相对路径
                try:
                    relative_path = str(item.relative_to(self.working_dir))
                except ValueError:
                    relative_path = str(item)
                
                # 获取文件大小
                try:
                    size = item.stat().st_size if item.is_file() else 0
                except (OSError, PermissionError):
                    size = 0
                
                # 添加到缓存
                file_item = FileItem(
                    name=item.name,
                    path=str(item),
                    relative_path=relative_path,
                    is_dir=item.is_dir(),
                    icon=self._get_file_icon(item),
                    size=size
                )
                self._file_cache.append(file_item)
                
                # 递归扫描子目录
                if item.is_dir():
                    self._scan_directory(item, depth + 1, max_depth)
                    
        except (PermissionError, OSError):
            pass
    
    def _get_file_icon(self, path: Path) -> str:
        """获取文件图标"""
        if path.is_dir():
            return "📁"
        
        suffix = path.suffix.lower()
        icon_map = {
            '.py': '🐍',
            '.js': '🟨', '.jsx': '🟨',
            '.ts': '🔷', '.tsx': '🔷',
            '.html': '🌐', '.htm': '🌐',
            '.css': '🎨', '.scss': '🎨', '.sass': '🎨',
            '.json': '📋',
            '.md': '📝', '.markdown': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.svg': '🖼️',
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.rar': '📦',
            '.exe': '⚙️', '.app': '⚙️',
            '.sh': '🔧', '.bat': '🔧', '.cmd': '🔧',
            '.yml': '⚙️', '.yaml': '⚙️',
            '.xml': '📜',
            '.sql': '🗄️',
            '.cpp': '⚡', '.c': '⚡', '.h': '⚡',
            '.java': '☕',
            '.go': '🐹',
            '.rs': '🦀',
            '.php': '🐘',
            '.rb': '💎',
            '.swift': '🐦',
            '.kt': '🎯',
        }
        
        return icon_map.get(suffix, '📄')
    
    def _format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}K"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f}M"
        else:
            return f"{size/(1024*1024*1024):.1f}G"
    
    def _fuzzy_match(self, query: str, text: str) -> Tuple[bool, int]:
        """模糊匹配算法"""
        query = query.lower()
        text = text.lower()
        
        # 精确匹配
        if query == text:
            return True, 100
        
        # 开头匹配
        if text.startswith(query):
            return True, 90
        
        # 包含匹配
        if query in text:
            return True, 70
        
        # 模糊字符匹配（按顺序出现）
        query_idx = 0
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
        
        if query_idx == len(query):
            return True, 50
        
        return False, 0
    
    def get_completions(self, document: Document, complete_event):
        """获取补全建议"""
        # 刷新缓存（如果需要）
        if not self._cache_valid:
            self._refresh_file_cache()
        
        text = document.text_before_cursor
        
        # 查找最后一个 @ 符号
        match = re.search(r'@([^\s]*)$', text)
        if not match:
            return
        
        query = match.group(1)  # @ 后面的文本
        
        # 如果没有输入任何内容（只有 @），显示所有文件
        if not query:
            # 显示所有文件（限制数量）
            for file_item in self._file_cache[:30]:
                yield self._create_completion(file_item, "")
            return
        
        # 过滤和排序文件
        matches: List[Tuple[FileItem, int]] = []
        for file_item in self._file_cache:
            # 尝试匹配文件名
            is_match, score = self._fuzzy_match(query, file_item.name)
            if is_match:
                matches.append((file_item, score))
                continue
            
            # 尝试匹配相对路径
            is_match, score = self._fuzzy_match(query, file_item.relative_path)
            if is_match:
                matches.append((file_item, score - 10))  # 路径匹配优先级稍低
        
        # 按分数排序
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # 限制结果数量
        matches = matches[:30]
        
        # 生成补全建议
        for file_item, score in matches:
            yield self._create_completion(file_item, query)
    
    def _create_completion(self, file_item: FileItem, query: str):
        """创建补全项"""
        # 补全文本（只补全文件名部分）
        completion_text = file_item.name
        
        # 主显示文本（更简洁）
        display_name = file_item.name
        
        # 元信息（显示在右侧）
        if file_item.is_dir:
            meta_info = "目录"
        else:
            meta_info = self._format_file_size(file_item.size)
        
        # 完整显示（图标 + 文件名）
        display = f"{file_item.icon}  {display_name}"
        
        return Completion(
            text=completion_text,
            start_position=-len(query),
            display=display,
            display_meta=meta_info,  # 显示在右侧的元信息
        )


class SmartFileInput:
    """智能文件输入处理器"""
    
    def __init__(self, working_dir: str = None, history_file: str = None):
        self.working_dir = Path(working_dir or os.getcwd())
        
        if HAS_PROMPT_TOOLKIT:
            # 使用 prompt_toolkit
            self.completer = FileCompleter(str(self.working_dir))
            
            # 历史记录文件
            if history_file is None:
                history_file = str(self.working_dir / '.dnm_history')
            self.history = FileHistory(history_file)
        else:
            self.completer = None
            self.history = None
    
    def get_input(self, prompt_text: str = "👤 你: ") -> str:
        """获取用户输入（带自动补全）"""
        if not HAS_PROMPT_TOOLKIT:
            # 降级到简单输入
            return self._fallback_input(prompt_text)
        
        try:
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.styles import Style
            from prompt_toolkit.completion import WordCompleter
            
            # 创建键绑定
            kb = KeyBindings()
            
            # Ctrl+Space 手动触发补全
            @kb.add('c-space')
            def _(event):
                """手动触发补全菜单"""
                event.current_buffer.start_completion()
            
            # 自定义样式 - 更美观的补全菜单
            custom_style = Style.from_dict({
                'completion-menu': 'bg:#1e1e1e #ffffff',  # 深色背景，白色文字
                'completion-menu.completion': 'bg:#1e1e1e #d4d4d4',  # 未选中项
                'completion-menu.completion.current': 'bg:#0066cc #ffffff bold',  # 选中项：蓝色背景
                'completion-menu.meta.completion': 'bg:#1e1e1e #888888',  # 元数据（图标）
                'completion-menu.meta.completion.current': 'bg:#0066cc #ffffff',  # 选中项元数据
                'scrollbar.background': 'bg:#1e1e1e',  # 滚动条背景
                'scrollbar.button': 'bg:#0066cc',  # 滚动条按钮
            })
            
            result = prompt(
                prompt_text,
                completer=self.completer,
                complete_while_typing=True,  # 输入时自动补全
                history=self.history,
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True,
                key_bindings=kb,
                # 补全菜单配置
                complete_in_thread=False,  # 同步补全，更即时
                mouse_support=True,  # 启用鼠标支持
                style=custom_style,  # 应用自定义样式
                # 重要：这些设置让补全立即显示
                complete_style='MULTI_COLUMN',  # 多列显示
                # 让补全菜单立即显示，不需要按 Tab
                reserve_space_for_menu=8,  # 为补全菜单预留空间
            )
            return result.strip()
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception as e:
            print(f"⚠️  输入增强功能出错，降级到简单模式: {e}")
            return self._fallback_input(prompt_text)
    
    def _fallback_input(self, prompt_text: str) -> str:
        """降级输入方法（不带自动补全）"""
        user_input = input(prompt_text).strip()
        
        # 如果包含 @，智能处理文件引用
        if '@' in user_input:
            return self._handle_at_symbol_fallback(user_input)
        
        return user_input
    
    def _show_popup_selector(self, matches: List[Dict], query: str) -> Optional[str]:
        """显示弹出式文件选择器（降级模式）"""
        print()
        print("┌" + "─" * 68 + "┐")
        print("│" + f" 🔍 找到 {len(matches)} 个匹配 '@{query}' 的文件".ljust(67) + "│")
        print("├" + "─" * 68 + "┤")
        
        # 显示文件列表
        for i, file in enumerate(matches[:15], 1):  # 最多显示15个
            icon = file['icon']
            name = file['name']
            type_str = "目录" if file['is_dir'] else ""
            
            # 高亮显示
            display_name = name
            if query.lower() in name.lower():
                # 简单高亮（用 [] 标记）
                idx = name.lower().index(query.lower())
                display_name = name[:idx] + f"[{name[idx:idx+len(query)]}]" + name[idx+len(query):]
            
            line = f"│ {i:2d}. {icon} {display_name:<50} {type_str:>8} │"
            # 确保行宽度一致
            line = line[:70] + "│"
            print(line)
        
        if len(matches) > 15:
            print("│" + f" ... 还有 {len(matches) - 15} 个文件（请输入更精确的搜索）".ljust(67) + "│")
        
        print("└" + "─" * 68 + "┘")
        print()
        print("💡 提示: 输入数字选择文件，或按 Enter 使用第一个匹配")
        
        return None
    
    def _handle_at_symbol_fallback(self, user_input: str) -> str:
        """处理 @ 符号（降级模式）- 增强弹出选择"""
        # 查找所有 @ 引用
        at_matches = re.finditer(r'@([^\s]+)', user_input)
        result = user_input
        
        for match in at_matches:
            query = match.group(1)
            full_match = match.group(0)  # 包含 @
            
            # 简单搜索文件
            matches = self._simple_file_search(query)
            
            if not matches:
                print(f"\n⚠️  未找到匹配 '@{query}' 的文件")
                continue
            
            if len(matches) == 1:
                # 唯一匹配，自动替换
                file = matches[0]
                print(f"✅ 自动选择: {file['icon']} {file['name']}")
                result = result.replace(full_match, f"@{file['name']}", 1)
                continue
            
            # 多个匹配，显示弹出式选择器
            self._show_popup_selector(matches, query)
            
            try:
                choice = input("👉 选择文件 (数字/Enter 用第一个/s 跳过): ").strip()
                
                if not choice or choice == '1':
                    # 默认选择第一个
                    file = matches[0]
                    print(f"✅ 已选择: {file['icon']} {file['name']}\n")
                    result = result.replace(full_match, f"@{file['name']}", 1)
                elif choice.lower() == 's':
                    # 跳过，保持原样
                    print(f"⏭️  跳过 @{query}\n")
                    continue
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < min(len(matches), 15):
                        file = matches[idx]
                        print(f"✅ 已选择: {file['icon']} {file['name']}\n")
                        result = result.replace(full_match, f"@{file['name']}", 1)
                    else:
                        print(f"❌ 无效选择，保持原样\n")
                else:
                    print(f"❌ 无效输入，保持原样\n")
                    
            except (ValueError, KeyboardInterrupt):
                print(f"\n⏭️  已跳过选择\n")
                continue
        
        return result
    
    def _simple_file_search(self, query: str) -> List[Dict]:
        """简单的文件搜索"""
        query_lower = query.lower()
        matches = []
        
        try:
            for item in self.working_dir.iterdir():
                if item.name.startswith('.'):
                    continue
                
                name_lower = item.name.lower()
                
                # 匹配逻辑
                score = 0
                if name_lower == query_lower:
                    score = 100
                elif name_lower.startswith(query_lower):
                    score = 90
                elif query_lower in name_lower:
                    score = 70
                
                if score > 0:
                    matches.append({
                        'name': item.name,
                        'path': str(item),
                        'is_dir': item.is_dir(),
                        'icon': self._get_simple_icon(item),
                        'score': score
                    })
            
            # 按分数排序
            matches.sort(key=lambda x: x['score'], reverse=True)
            return matches[:20]
            
        except (PermissionError, OSError):
            return []
    
    def _get_simple_icon(self, path: Path) -> str:
        """简单的文件图标"""
        if path.is_dir():
            return "📁"
        
        suffix = path.suffix.lower()
        if suffix == '.py':
            return '🐍'
        elif suffix in ['.js', '.jsx']:
            return '🟨'
        elif suffix in ['.md', '.markdown']:
            return '📝'
        elif suffix == '.json':
            return '📋'
        else:
            return '📄'


# 全局实例
smart_input = SmartFileInput()


def update_smart_input_directory(new_dir: str):
    """更新工作目录"""
    global smart_input
    smart_input = SmartFileInput(new_dir)


def get_smart_input(prompt_text: str = "👤 你: ") -> str:
    """获取智能输入的便捷函数"""
    return smart_input.get_input(prompt_text)


def check_prompt_toolkit_available() -> bool:
    """检查 prompt_toolkit 是否可用"""
    return HAS_PROMPT_TOOLKIT

