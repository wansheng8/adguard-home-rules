"""步骤⑤ 去重：按规范化后的域名去重；黑白名单冲突处理。"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any


def normalize_domain(domain: str) -> str:
    """规范化域名：小写、去尾点。"""
    return domain.strip().lower().rstrip(".")


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按域名去重；正则等无域名规则按原始行去重。

    规则：
    - DNS 层广告拦截优先 —— 若同一域名同时出现在黑白名单，保留黑名单。
      （浏览器例外白名单会放行广告域名解析；DNS 过滤以拦截为准，
        确需放行的正常服务域名由白名单产物单独输出，不覆盖黑名单。）
    - 无域名的规则（正则/部分通配符）按 raw 精确去重，不丢弃。
    - 其余情况保留首个出现的记录。
    """
    seen_domain: OrderedDict[str, dict[str, Any]] = OrderedDict()
    seen_raw: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for rec in records:
        domain = normalize_domain(rec.get("domain", ""))
        if not domain:
            raw = rec.get("raw", "")
            if raw and raw not in seen_raw:
                seen_raw[raw] = rec
            continue
        if domain in seen_domain:
            existing = seen_domain[domain]
            if rec["action"] == "blacklist" and existing["action"] != "blacklist":
                seen_domain[domain] = rec
            continue
        seen_domain[domain] = rec
    return list(seen_domain.values()) + list(seen_raw.values())


def dedupe_by_raw(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按原始行精确去重（用于保输出原文的产物）。"""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for rec in records:
        key = rec.get("raw", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(rec)
    return out
