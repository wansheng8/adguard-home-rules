"""步骤③ 语法过滤：按 syntax.yaml 定义的 AdGuard Home 语法识别并分类每条规则。

输入：原始规则行列表
输出：rule 记录列表，每条含
  {
    "raw": 原始文本,
    "domain": 提取的纯域名（无修饰符；正则等无域名的为空）,
    "action": "whitelist" | "blacklist",
    "output": "adblock" | "hosts" | "none",
    "rule_type": 命中的规则类型名称,
    "source": 来源索引,
    "category": 分类,
    "keep_raw": 生成时是否保留原始文本（正则/通配符/带修饰符规则）,
  }
"""
from __future__ import annotations

import ipaddress
import re
from typing import Any

try:
    import idna
except ImportError:
    idna = None

from ..config import load_syntax


class RuleClassifier:
    """基于 syntax.yaml 规则类型的分类器。"""

    def __init__(self, syntax: dict[str, Any]):
        self.syntax = syntax
        self.rule_types = syntax.get("rule_types", {})
        self.reserved = set(syntax.get("reserved_hosts", []))
        self.category_keywords = syntax.get("category_keywords", {})
        self.supported_modifiers = syntax.get("supported_modifiers", [])
        self.unsupported_patterns = syntax.get("unsupported_patterns", [])
        self._patterns = {}
        for name, spec in self.rule_types.items():
            pat = spec.get("pattern", "")
            if pat:
                self._patterns[name] = re.compile(pat, re.IGNORECASE)

    # ---------- 语法校验 ----------

    @staticmethod
    def _valid_domain(domain: str) -> bool:
        """校验是否为合法 DNS 域名。"""
        domain = domain.strip().rstrip(".")
        if len(domain) > 253:
            return False
        try:
            ipaddress.ip_address(domain)
            return False  # 纯 IP 不作为域名规则
        except ValueError:
            pass
        labels = domain.split(".")
        if len(labels) < 2:
            return False
        for label in labels:
            if not 1 <= len(label) <= 63:
                return False
            if not re.match(r"^[a-z0-9_\-]+$", label, re.IGNORECASE):
                return False
            if label.startswith("-") or label.endswith("-"):
                return False
        return True

    @staticmethod
    def _to_punycode(domain: str) -> str:
        """国际化域名转 punycode；失败则原样返回。"""
        if not idna or not any(ord(c) > 127 for c in domain):
            return domain
        try:
            return idna.encode(domain).decode("ascii")
        except Exception:
            return domain

    # ---------- 语法提取 ----------

    @staticmethod
    def _extract_host(line: str) -> str:
        """从规则行提取纯域名主体。

        处理：@@ || | 前缀、协议前缀、* 通配符、^ 尾分隔符、$ 修饰符。
        返回空字符串表示无法提取（如纯路径规则）。
        """
        text = line
        text = re.sub(r"^@@", "", text)          # 白名单标记
        text = re.sub(r"^\|+", "", text)         # || 或 | 前缀
        text = re.sub(r"^[a-z][a-z0-9+\-]*://", "", text, flags=re.IGNORECASE)  # 协议
        text = re.sub(r"^\*+\.?", "", text)      # 通配符 * 或 *.
        text = text.split("$", 1)[0]             # 去掉修饰符
        text = text.split("/", 1)[0]             # 去掉路径（DNS 层无效）
        text = text.rstrip("^|")                 # 尾分隔符 ^ 或尾部竖线 |
        return text.strip().lower()

    def _has_path(self, line: str) -> bool:
        """判断规则是否含路径过滤（DNS 层不支持 → 忽略）。

        正则规则 /.../ 虽然含 /，但不属于路径过滤，调用方已排除。
        """
        if "/" not in line:
            return False
        text = re.sub(r"^@@", "", line)
        text = re.sub(r"^\|+", "", text)
        text = re.sub(r"^[a-z][a-z0-9+\-]*://", "", text, flags=re.IGNORECASE)
        return "/" in text.split("$", 1)[0]

    def _unsupported_modifier(self, line: str) -> bool:
        """判断修饰符部分是否包含不支持的浏览器专用修饰符。"""
        if "$" not in line:
            return False
        return any(p in line for p in self.unsupported_patterns)

    def _any_unsupported(self, line: str) -> bool:
        """命中不支持的语法特征（元素隐藏/脚本注入/浏览器修饰符等）。"""
        for pat in self.unsupported_patterns:
            if pat in line:
                return True
        return False

    # ---------- 主入口 ----------

    def classify(self, raw_line: str, source: str = "") -> dict[str, Any] | None:
        """识别单条规则，返回规则记录；无法识别/应忽略时返回 None。"""
        line = raw_line.strip()
        if not line:
            return None

        # 不支持的语法（元素隐藏、脚本注入、浏览器修饰符等）→ 忽略
        if self._any_unsupported(line):
            return None

        record: dict[str, Any] = {
            "raw": raw_line.rstrip("\n"),
            "domain": "",
            "action": "ignore",
            "output": "none",
            "rule_type": "",
            "source": source,
            "category": "other",
            "keep_raw": False,
        }

        # 依序匹配规则类型
        for name, spec in self.rule_types.items():
            pat = self._patterns.get(name)
            if not pat:
                continue
            if not pat.match(line):
                continue
            action = spec.get("action", "ignore")
            if action == "ignore":
                return None
            record["action"] = action
            record["output"] = spec.get("output", "adblock")
            record["rule_type"] = name
            record["keep_raw"] = bool(spec.get("keep_raw", False))

            # 路径过滤 → 忽略（DNS 层看不到 URL 路径）；正则规则除外
            if name != "regex_rule" and self._has_path(line):
                return None

            # 通配符规则原样保留
            if "*" in line:
                record["keep_raw"] = True

            # 带修饰符的规则：检查修饰符是否受支持（正则规则除外，其 $ 是锚点）
            if (
                "$" in line
                and name not in ("hosts_rule", "hosts_reversed", "regex_rule")
            ):
                mods = line.split("$", 1)[1].split(",")
                for mod in mods:
                    key = mod.split("=", 1)[0].strip()
                    if key and key not in self.supported_modifiers:
                        return None

            # hosts 规则从 "IP domain" / "domain IP" 中提取域名
            if name == "hosts_rule":
                domain = re.sub(r"^((0\.0\.0\.0|127\.0\.0\.1|::1|::)[ \t]+)", "", line).strip()
            elif name == "hosts_reversed":
                domain = re.sub(
                    r"[ \t]+(0\.0\.0\.0|127\.0\.0\.1|::1|::)$", "", line
                ).strip()
            else:
                domain = self._extract_host(line)
            record["domain"] = domain

            if domain:
                record["domain"] = self._to_punycode(domain)
                if record["domain"].lower() in self.reserved:
                    return None
                if not self._valid_domain(record["domain"]):
                    return None
            record["category"] = self._guess_category(record["domain"] or line)
            return record

        # 未匹配任何类型：默认忽略
        return None

    def _guess_category(self, text: str) -> str:
        """按关键词猜测分类。"""
        low = text.lower()
        for category, keywords in self.category_keywords.items():
            if not keywords:
                continue
            if any(k in low for k in keywords):
                return category
        return "other"


def filter_rules(lines: list[str], syntax: dict[str, Any], source: str = "") -> list[dict[str, Any]]:
    """对原始行列表执行语法过滤。"""
    classifier = RuleClassifier(syntax)
    records = []
    for line in lines:
        rec = classifier.classify(line, source)
        if rec:
            records.append(rec)
    return records
