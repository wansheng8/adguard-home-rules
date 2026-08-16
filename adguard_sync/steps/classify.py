"""步骤④ 分类：基于 syntax.yaml 的 category_keywords 或源自带 category 标记规则分类。"""
from __future__ import annotations

from typing import Any


def classify_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """为每条规则记录补充/确认 category。

    优先级：源配置自带 category > 语法层关键词猜测。
    若语法层已给出非 other 分类则保留。
    """
    for rec in records:
        source_category = rec.get("source_category", "")
        if source_category and rec.get("category", "other") == "other":
            rec["category"] = source_category
    return records
