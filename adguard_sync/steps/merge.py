"""步骤⑥ 合并：分离黑白名单记录，产出最终黑名单/白名单集合。"""
from __future__ import annotations

from typing import Any


def split_by_action(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """将规则记录按 action 拆分。"""
    blacklist = [r for r in records if r["action"] == "blacklist"]
    whitelist = [r for r in records if r["action"] == "whitelist"]
    return {"blacklist": blacklist, "whitelist": whitelist}
