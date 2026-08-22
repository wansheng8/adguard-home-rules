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
    """生成订阅源链接清单。

    风格：| 过滤器类型 | 完整版 | 精简版 |
    完整版 = GitHub 源链接（raw.githubusercontent.com）
    精简版 = CDN 加速链接（cdn.jsdelivr.net）
    """
    links = manifest.get("links", [])
    if not links:
        return "> 尚未生成产物，请先运行流水线。"

    # 产物文件 -> 过滤器类型名称（用于展示）
    file_type_map = {
        "adblock.txt": "广告过滤器",
        "黑名单.txt": "DNS过滤器",
        "hosts.txt": "Host列表",
        "白名单.txt": "白名单",
    }

    # 每个文件的两类链接
    file_urls: dict[str, dict[str, str]] = {}
    for item in links:
        file_urls.setdefault(item["file"], {})[item["cdn"]] = item["url"]

    lines = []
    lines.append("| 过滤器类型 | 完整版 | 精简版 |")
    lines.append("| --- | --- | --- |")
    for file_name, type_name in file_type_map.items():
        urls = file_urls.get(file_name, {})
        github = urls.get("raw.githubusercontent.com")
        cdn = urls.get("cdn.jsdelivr.net")
        if not github or not cdn:
            continue
        full = f"[Github]({github})"
        lite = f"[CDN]({cdn})"
        lines.append(f"| {type_name} | {full} | {lite} |")
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
    lines.append("")
    lines.append("## 使用方式（AdGuard Home）")
    lines.append("")
    lines.append("在 AdGuard Home 的「过滤器 → DNS 拦截清单」中添加上表中的链接即可订阅：")
    lines.append("")
    lines.append("1. 打开 AdGuard Home 管理面板")
    lines.append("2. 进入 **过滤器** → **DNS 拦截清单** → **添加过滤器**")
    lines.append("3. 粘贴上表中的订阅链接（推荐 **广告过滤器** 或 **DNS过滤器**）")
    lines.append("4. 若需放行误拦域名，同时订阅 **白名单**")
    lines.append("")
    lines.append("> 提示：国内环境可优先选用 `cdn.jsdelivr.net` 加速链接。")
    lines.append("")
    lines.append("## IPv4/IPv6 配置说明")
    lines.append("")
    lines.append("本仓库的 **adblock 与 hosts 规则对 IPv4（A）和 IPv6（AAAA）查询均生效**。")
    lines.append("订阅后在「过滤器 → DNS 拦截清单」正常拦截两种记录，无需单独处理 IPv6。")
    lines.append("若设备仍能加载广告，请按以下顺序排查配置层绕过：")
    lines.append("")
    lines.append("1. **确认 DNS 走 AdGuard Home**：设备 DNS 若指向运营商/路由器，或启用了 Android「私人 DNS」等加密 DNS（DoH/DoT），请求不经过本过滤器，全部失效。")
    lines.append("2. **AdGuard Home 监听地址**：在「设置 → DNS 设置 → 监听接口」中确保同时监听 IPv4 与 IPv6（如 `0.0.0.0` 与 `::`），否则仅 IPv6 设备（如部分手机默认 IPv6）的查询不受控。")
    lines.append("3. **阻断方式（Blocking mode）**：在「设置 → DNS 设置」中选用 **Null IP** 或 **NXDOMAIN**。Null IP 会对 A 返回 `0.0.0.0`、对 AAAA 返回 `::`，两种记录都被拦；若误用自定义 IP 且仅填写 IPv4，AAAA 查询将放行。")
    lines.append("4. **IPv6 上游**：若启用 IPv6 上游或路由器下发了 IPv6 DNS，确认客户端实际使用的解析服务器仍是 AdGuard Home。")
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
