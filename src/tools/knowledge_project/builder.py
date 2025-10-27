"""
知识库构建器

职责：
- 扫描工作目录下的文档与代码
- 抽取基本知识项（文件/模块、类、函数、配置键）与关系（defined_in）
- 生成内存结构，供导出器落盘

仅使用标准库，保证在受限网络/环境下可运行。
"""

from __future__ import annotations

import ast
import json
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any


DEFAULT_INCLUDE = (".md", ".py", ".json")
DEFAULT_EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".idea", ".cursor", ".claude"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB 上限，避免误读大文件


def _hash_id(*parts: str) -> str:
    h = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()
    return h[:12]


def list_files(work_dir: str, include_suffix: Tuple[str, ...] = DEFAULT_INCLUDE) -> List[Path]:
    files: List[Path] = []
    base = Path(work_dir)
    for root, dirnames, filenames in os.walk(base):
        # 过滤目录
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]
        for fn in filenames:
            p = Path(root) / fn
            try:
                if not p.is_file():
                    continue
                if p.suffix.lower() not in include_suffix:
                    continue
                if p.stat().st_size > MAX_FILE_SIZE:
                    continue
                files.append(p)
            except Exception:
                # 读元信息失败则跳过
                continue
    return files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return path.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return ""


def parse_markdown(path: Path) -> List[Dict[str, Any]]:
    """抽取 Markdown 的标题作为知识项；首段作为摘要。"""
    text = _read_text(path)
    if not text:
        return []
    items: List[Dict[str, Any]] = []

    # 摘要：前 400 字符
    summary = re.sub(r"\s+", " ", text.strip())[:400]

    # 标题项
    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            if not title:
                continue
            item_id = _hash_id(str(path), f"h{level}:{title}")
            items.append({
                "id": item_id,
                "type": "heading",
                "title": title,
                "level": level,
                "source": str(path),
                "summary": summary,
            })

    # 文件级项
    file_item_id = _hash_id(str(path))
    items.insert(0, {
        "id": file_item_id,
        "type": "document",
        "title": path.name,
        "source": str(path),
        "summary": summary,
    })

    return items


def parse_python(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """抽取 Python 的模块/类/函数为知识项，并生成 defined_in 关系。"""
    text = _read_text(path)
    if not text:
        return [], []

    items: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []

    try:
        tree = ast.parse(text)
    except Exception:
        # 语法异常时，降级为仅文件级项
        file_item_id = _hash_id(str(path))
        items.append({
            "id": file_item_id,
            "type": "module",
            "title": path.stem,
            "source": str(path),
            "summary": text.strip()[:400],
        })
        return items, relations

    # 模块文档
    module_doc = ast.get_docstring(tree) or ""
    module_id = _hash_id(str(path))
    items.append({
        "id": module_id,
        "type": "module",
        "title": path.stem,
        "source": str(path),
        "summary": (module_doc or text.strip()[:400]),
    })

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            doc = ast.get_docstring(node) or ""
            cid = _hash_id(str(path), f"class:{node.name}")
            items.append({
                "id": cid,
                "type": "class",
                "title": node.name,
                "source": str(path),
                "summary": (doc or f"Python 类 {node.name}"),
            })
            relations.append({
                "type": "defined_in",
                "from": cid,
                "to": module_id,
            })
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            doc = ast.get_docstring(node) or ""
            fid = _hash_id(str(path), f"func:{node.name}")
            items.append({
                "id": fid,
                "type": "function",
                "title": node.name,
                "source": str(path),
                "summary": (doc or f"Python 函数 {node.name}"),
            })
            relations.append({
                "type": "defined_in",
                "from": fid,
                "to": module_id,
            })
            self.generic_visit(node)

    Visitor().visit(tree)

    return items, relations


def parse_json_file(path: Path) -> List[Dict[str, Any]]:
    """抽取 JSON 顶层键作为配置项。"""
    text = _read_text(path)
    if not text:
        return []
    try:
        data = json.loads(text)
    except Exception:
        return []

    items: List[Dict[str, Any]] = []
    file_id = _hash_id(str(path))
    items.append({
        "id": file_id,
        "type": "config",
        "title": path.name,
        "source": str(path),
        "summary": f"JSON 配置文件，顶层键: {', '.join(list(data.keys())[:10]) if isinstance(data, dict) else 'N/A'}",
    })
    if isinstance(data, dict):
        for k, v in list(data.items())[:50]:  # 限顶 50 个
            kid = _hash_id(str(path), f"key:{k}")
            vtype = type(v).__name__
            items.append({
                "id": kid,
                "type": "config_key",
                "title": f"{k}",
                "source": str(path),
                "summary": f"类型: {vtype}",
            })
    return items


def build_knowledge_base(work_dir: str) -> Dict[str, Any]:
    """构建知识库内存结构。"""
    files = list_files(work_dir)
    items: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []

    for p in files:
        suffix = p.suffix.lower()
        if suffix == ".md":
            items.extend(parse_markdown(p))
        elif suffix == ".py":
            its, rels = parse_python(p)
            items.extend(its)
            relations.extend(rels)
        elif suffix == ".json":
            items.extend(parse_json_file(p))

    # 去重（按 id ）
    uniq: Dict[str, Dict[str, Any]] = {}
    for it in items:
        uniq[it["id"]] = it
    items = list(uniq.values())

    kb = {
        "version": 1,
        "work_dir": str(Path(work_dir).absolute()),
        "stats": {
            "items": len(items),
            "relations": len(relations),
            "files_scanned": len(files),
        },
        "items": items,
        "relations": relations,
    }
    return kb

