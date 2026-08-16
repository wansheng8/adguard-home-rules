"""步骤② 清洗：去 BOM/空白/注释行/无效行，统一行尾。"""
from __future__ import annotations

import re

COMMENT_PREFIXES = ("#", "!", "[", "/", "*")


def clean_lines(lines: list[str]) -> list[str]:
    """清洗原始行：
    - 去除 BOM
    - 去除首尾空白
    - 去除纯注释行与空行
    - 去除内联注释（以 # 或 ! 开头视为整行注释；行内 # 注释暂保留给语法层处理）
    """
    cleaned: list[str] = []
    for line in lines:
        line = line.replace("\ufeff", "")
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(COMMENT_PREFIXES):
            continue
        cleaned.append(stripped)
    return cleaned
