"""
知识库导出器

将内存中的知识库结构导出到目录 knowledge/：
- kb.json: 完整知识库结构
- cards/: 每个知识项一个 Markdown 卡片
- README.md: 简要索引
- graph.csv: 边列表（type,from,to）
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Any


def ensure_dir(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)


def export_kb(work_dir: str, kb: Dict[str, Any]) -> str:
    base = Path(work_dir) / "knowledge"
    ensure_dir(base)

    # 1) kb.json
    kb_path = base / "kb.json"
    kb_path.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) cards
    cards_dir = base / "cards"
    ensure_dir(cards_dir)
    for it in kb.get("items", []):
        card = _format_card(it)
        (cards_dir / f"{it['id']}.md").write_text(card, encoding="utf-8")

    # 3) README
    readme = _format_index_md(kb)
    (base / "README.md").write_text(readme, encoding="utf-8")

    # 4) graph.csv
    graph_path = base / "graph.csv"
    _export_graph_csv(graph_path, kb)

    return str(base)


def _format_card(it: Dict[str, Any]) -> str:
    title = it.get("title", "")
    itype = it.get("type", "")
    source = it.get("source", "")
    summary = it.get("summary", "")
    lines = [
        f"# {title}",
        "",
        f"- 类型: {itype}",
        f"- 来源: {source}",
        "",
        "## 摘要",
        summary or "(无)",
        "",
    ]
    return "\n".join(lines)


def _format_index_md(kb: Dict[str, Any]) -> str:
    stats = kb.get("stats", {})
    items = kb.get("items", [])

    # 简单分组
    by_type: Dict[str, int] = {}
    for it in items:
        t = it.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    lines = [
        "# 知识库索引",
        "",
        f"- 项目: {kb.get('work_dir', '')}",
        f"- 知识项: {stats.get('items', 0)}",
        f"- 关系: {stats.get('relations', 0)}",
        f"- 扫描文件数: {stats.get('files_scanned', 0)}",
        "",
        "## 类型分布",
    ]
    for t, n in sorted(by_type.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {t}: {n}")

    lines.append("")
    lines.append("## 示例卡片 (前20)")
    for it in items[:20]:
        lines.append(f"- [{it.get('title','')}](cards/{it['id']}.md)")

    return "\n".join(lines)


def _export_graph_csv(path: Path, kb: Dict[str, Any]) -> None:
    rels = kb.get("relations", [])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "from", "to"])
        for r in rels:
            writer.writerow([r.get("type", ""), r.get("from", ""), r.get("to", "")])

