"""
文件引用解析器模块
支持 @ 语法引用文件，提供智能文件匹配和路径解析功能
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FileReference:
    """文件引用信息"""
    original_text: str      # 原始 @文件名 文本
    file_path: str         # 解析后的文件路径
    exists: bool           # 文件是否存在
    is_directory: bool     # 是否为目录
    match_confidence: float # 匹配置信度 (0-1)


class FileReferenceParser:
    """文件引用解析器"""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = Path(working_dir or os.getcwd())
        self.max_search_depth = 3  # 最大搜索深度
        
    def parse_references(self, text: str) -> Tuple[str, List[FileReference]]:
        """
        解析文本中的文件引用
        
        Args:
            text: 包含 @ 引用的文本
            
        Returns:
            (processed_text, file_references): 处理后的文本和文件引用列表
        """
        # 匹配 @ 引用的正则表达式
        # 支持: @filename, @./path/file, @/abs/path, @*.ext, @folder/
        pattern = r'@([^\s@]+(?:\.[a-zA-Z0-9]+)?/?(?:\*\.[a-zA-Z0-9]+)?)'
        
        matches = re.finditer(pattern, text)
        references = []
        processed_text = text
        
        for match in matches:
            ref_text = match.group(0)  # 完整的 @reference
            file_pattern = match.group(1)  # 文件模式部分
            
            # 解析文件引用
            file_refs = self._resolve_file_pattern(ref_text, file_pattern)
            references.extend(file_refs)
            
            # 替换文本中的引用为更友好的描述
            if file_refs:
                best_ref = max(file_refs, key=lambda x: x.match_confidence)
                replacement = f"文件 '{best_ref.file_path}'"
                processed_text = processed_text.replace(ref_text, replacement, 1)
        
        return processed_text, references
    
    def _resolve_file_pattern(self, original_text: str, pattern: str) -> List[FileReference]:
        """解析文件模式，返回匹配的文件列表"""
        references = []
        
        # 处理不同类型的路径
        if pattern.startswith('/'):
            # 绝对路径
            references.extend(self._match_absolute_path(original_text, pattern))
        elif pattern.startswith('./') or pattern.startswith('../'):
            # 相对路径
            references.extend(self._match_relative_path(original_text, pattern))
        elif '*' in pattern:
            # 通配符模式
            references.extend(self._match_wildcard_pattern(original_text, pattern))
        else:
            # 简单文件名，需要智能搜索
            references.extend(self._smart_file_search(original_text, pattern))
        
        return references
    
    def _match_absolute_path(self, original_text: str, pattern: str) -> List[FileReference]:
        """匹配绝对路径"""
        path = Path(pattern)
        return [FileReference(
            original_text=original_text,
            file_path=str(path),
            exists=path.exists(),
            is_directory=path.is_dir() if path.exists() else False,
            match_confidence=1.0 if path.exists() else 0.0
        )]
    
    def _match_relative_path(self, original_text: str, pattern: str) -> List[FileReference]:
        """匹配相对路径"""
        path = self.working_dir / pattern
        return [FileReference(
            original_text=original_text,
            file_path=str(path),
            exists=path.exists(),
            is_directory=path.is_dir() if path.exists() else False,
            match_confidence=1.0 if path.exists() else 0.0
        )]
    
    def _match_wildcard_pattern(self, original_text: str, pattern: str) -> List[FileReference]:
        """匹配通配符模式"""
        references = []
        try:
            # 在当前目录搜索
            matches = glob.glob(str(self.working_dir / pattern), recursive=True)
            for match in matches[:10]:  # 限制结果数量
                path = Path(match)
                references.append(FileReference(
                    original_text=original_text,
                    file_path=str(path),
                    exists=True,
                    is_directory=path.is_dir(),
                    match_confidence=0.9
                ))
        except Exception:
            pass
        
        return references
    
    def _smart_file_search(self, original_text: str, filename: str) -> List[FileReference]:
        """智能文件搜索"""
        references = []
        
        # 1. 精确匹配当前目录
        exact_path = self.working_dir / filename
        if exact_path.exists():
            references.append(FileReference(
                original_text=original_text,
                file_path=str(exact_path),
                exists=True,
                is_directory=exact_path.is_dir(),
                match_confidence=1.0
            ))
            return references
        
        # 2. 递归搜索匹配的文件
        found_files = self._recursive_search(filename)
        
        # 3. 模糊匹配
        if not found_files:
            found_files = self._fuzzy_search(filename)
        
        # 转换为 FileReference 对象
        for file_path, confidence in found_files:
            path = Path(file_path)
            references.append(FileReference(
                original_text=original_text,
                file_path=str(path),
                exists=True,
                is_directory=path.is_dir(),
                match_confidence=confidence
            ))
        
        return references
    
    def _recursive_search(self, filename: str) -> List[Tuple[str, float]]:
        """递归搜索文件"""
        matches = []
        
        def search_directory(directory: Path, depth: int = 0):
            if depth > self.max_search_depth:
                return
            
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.name == filename:
                        matches.append((str(item), 0.9 - depth * 0.1))
                    elif item.is_dir() and not item.name.startswith('.'):
                        search_directory(item, depth + 1)
            except (PermissionError, OSError):
                pass
        
        search_directory(self.working_dir)
        return matches
    
    def _fuzzy_search(self, filename: str) -> List[Tuple[str, float]]:
        """模糊匹配文件名"""
        matches = []
        filename_lower = filename.lower()
        
        def fuzzy_match_directory(directory: Path, depth: int = 0):
            if depth > self.max_search_depth:
                return
            
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        item_name_lower = item.name.lower()
                        
                        # 计算相似度
                        confidence = self._calculate_similarity(filename_lower, item_name_lower)
                        
                        if confidence > 0.6:  # 相似度阈值
                            matches.append((str(item), confidence - depth * 0.1))
                    
                    elif item.is_dir() and not item.name.startswith('.'):
                        fuzzy_match_directory(item, depth + 1)
            except (PermissionError, OSError):
                pass
        
        fuzzy_match_directory(self.working_dir)
        
        # 按相似度排序，返回前5个
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        # 简单的相似度计算
        if str1 == str2:
            return 1.0
        
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # 计算公共子序列长度
        common_chars = set(str1) & set(str2)
        if not common_chars:
            return 0.0
        
        return len(common_chars) / max(len(str1), len(str2))
    
    def get_file_suggestions(self, partial_name: str = "") -> List[str]:
        """获取文件建议列表（用于自动补全）"""
        suggestions = []
        
        try:
            # 获取当前目录的文件
            for item in self.working_dir.iterdir():
                if item.is_file():
                    if not partial_name or item.name.lower().startswith(partial_name.lower()):
                        suggestions.append(item.name)
            
            # 限制建议数量
            suggestions.sort()
            return suggestions[:20]
        except Exception:
            return []
    
    def format_reference_summary(self, references: List[FileReference]) -> str:
        """格式化文件引用摘要"""
        if not references:
            return "未找到文件引用"
        
        summary = "📁 文件引用解析结果:\n"
        for i, ref in enumerate(references, 1):
            status = "✅" if ref.exists else "❌"
            file_type = "📁" if ref.is_directory else "📄"
            confidence = f"({ref.match_confidence:.1%})"
            
            summary += f"  {i}. {status} {file_type} {ref.file_path} {confidence}\n"
        
        return summary


# 全局解析器实例
file_parser = FileReferenceParser()


def update_working_directory(new_dir: str):
    """更新工作目录"""
    global file_parser
    file_parser.working_dir = Path(new_dir)


def parse_file_references(text: str) -> Tuple[str, List[FileReference]]:
    """解析文件引用的便捷函数"""
    return file_parser.parse_references(text)


def get_file_suggestions(partial_name: str = "") -> List[str]:
    """获取文件建议的便捷函数"""
    return file_parser.get_file_suggestions(partial_name)
