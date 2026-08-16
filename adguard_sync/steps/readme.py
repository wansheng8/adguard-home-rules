"""步骤⑧ 构建 README.md：基于规则统计、产物链接自动生成。"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT, resolve_repo_name


def _beijing_now() -> datetime:
    import zoneinfo

    tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    return datetime.now(tz)


def _load_manifest(settings: dict[str, Any]) -> dict[str, Any]:
    out_dir = REPO_ROOT / settings["output"]["dir"]
    manifest_file = out_dir / "manifest.json"
    if manifest_file.exists():
        try:
            return json.loads(manifest_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _stats_table(records: dict[str, list[dict[str, Any]]], category_order: list[str]) -> str:
    """生成分类统计表格。"""
    black = records.get("blacklist", [])
    white = records.get("whitelist", [])
    from collections import Counter

    black_counter = Counter(r.get("category", "other") for r in black)
    white_counter = Counter(r.get("category", "other") for r in white)

    rows = []
    rows.append("| 分类 | 黑名单 | 白名单 |")
    rows.append("| --- | ---: | ---: |")
    total_b = total_w = 0
    for cat in category_order:
        b = black_counter.get(cat, 0)
        w = white_counter.get(cat, 0)
        total_b += b
        total_w += w
        rows.append(f"| {cat} | {b} | {w} |")
    rows.append(f"| **合计** | **{total_b}** | **{total_w}** |")
    return "\n".join(rows)


def _subscription_section(manifest: dict[str, Any]) -> str:
    """生成订阅源链接清单。"""
    links = manifest.get("links", [])
    if not links:
        return "> 尚未生成产物，请先运行流水线。"

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in links:
        grouped.setdefault(item["file"], []).append(item)

    lines = []
    for file_name, variants in grouped.items():
        lines.append(f"### `{file_name}`")
        lines.append("")
        lines.append("| CDN | 订阅链接 |")
        lines.append("| --- | --- |")
        for v in variants:
            lines.append(f"| {v['cdn']} | `{v['url']}` |")
        lines.append("")
    return "\n".join(lines)


def build_readme(
    merged: dict[str, list[dict[str, Any]]],
    settings: dict[str, Any],
    stats: dict[str, Any] | None = None,
) -> str:
    """构建 README.md 内容。"""
    manifest = _load_manifest(settings)
    owner, repo = resolve_repo_name(settings)
    homepage = f"https://github.com/{owner}/{repo}" if owner and repo else ""

    title = settings["readme"]["title"]
    description = settings["readme"]["description"]

    lines = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(description)
    lines.append("")
    lines.append("## 订阅链接")
    lines.append("")
    lines.append(_subscription_section(manifest))
    lines.append("## 使用方式（AdGuard Home）")
    lines.append("")
    lines.append("在 AdGuard Home 的「过滤器 → DNS 拦截清单」中添加上述链接即可订阅：")
    lines.append("")
    lines.append("1. 打开 AdGuard Home 管理面板")
    lines.append("2. 进入 **过滤器** → **DNS 拦截清单** → **添加过滤器**")
    lines.append("3. 粘贴上表中的任一订阅链接（推荐 `hosts.txt` 或 `adblock.txt`）")
    lines.append("4. 若需放行误拦域名，同时订阅 `whitelist.txt`")
    lines.append("")
    lines.append("> 提示：国内环境可优先选用 `cdn.jsdelivr.net` 加速链接。")
    lines.append("")
    lines.append("## 规则统计")
    lines.append("")
    lines.append(_stats_table(merged, settings.get("category_order", [])))
    lines.append("")
    lines.append("## 更新信息")
    lines.append("")
    lines.append(f"- 时区：北京时间 (Asia/Shanghai)")
    lines.append(f"- 更新频率：每 8 小时自动同步一次（GitHub Actions 定时任务）")
    lines.append(f"- 最近更新时间：{_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    if homepage:
        lines.append(f"[GitHub 仓库]({homepage})")
    lines.append("")
    return "\n".join(lines)


def write_readme(content: str) -> Path:
    """写入 README.md 到仓库根目录。"""
    target = REPO_ROOT / "README.md"
    target.write_text(content, encoding="utf-8")
    return target
