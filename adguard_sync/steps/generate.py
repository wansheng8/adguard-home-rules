"""步骤⑦ 生成：输出 hosts / adblock / blacklist / whitelist 文件与 CDN 链接清单。"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import resolve_repo_name
from .filter import RuleClassifier

ADGUARD_HEADER = """!
! Title: AdGuard Home 规则聚合订阅
! Description: {description}
! Generated: {time} (Asia/Shanghai)
! Homepage: {homepage}
! Licence: MIT
! ------------
"""


def _beijing_now() -> datetime:
    """返回北京时间当前时间。"""
    import zoneinfo

    tz = zoneinfo.ZoneInfo("Asia/Shanghai")
    return datetime.now(tz)


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _header(section: str, desc: str, homepage: str) -> str:
    return ADGUARD_HEADER.format(
        description=desc,
        time=_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
        homepage=homepage,
    ) + f"! Section: {section}\n"


def generate_hosts(records: list[dict[str, Any]], homepage: str) -> str:
    """生成 hosts 格式：每行 `0.0.0.0 domain`，仅含可提取域名的规则。"""
    lines = [_header("hosts", "纯域名黑名单（hosts 格式）", homepage)]
    lines.extend(
        "0.0.0.0 " + r["domain"]
        for r in records
        if r["domain"] and not r.get("keep_raw", False)
    )
    return "\n".join(lines) + "\n"


def generate_adblock(records: list[dict[str, Any]], homepage: str) -> str:
    """生成 AdGuard/adblock 语法。

    - 可提取域名的规则：||domain^
    - 正则/通配符/带修饰符规则：原样保留（keep_raw）
    """
    lines = [_header("adblock", "AdGuard/adblock 语法黑名单", homepage)]
    for r in records:
        if r.get("keep_raw", False):
            lines.append(r["raw"])
        elif r["domain"]:
            lines.append("||" + r["domain"] + "^")
    return "\n".join(lines) + "\n"


def generate_blacklist(records: list[dict[str, Any]], homepage: str) -> str:
    """合并黑名单（AdGuard 标准语法 ||domain^）。"""
    lines = [_header("blacklist", "全部黑名单（AdGuard 语法）", homepage)]
    lines.extend(
        "||" + r["domain"] + "^"
        for r in records
        if r["domain"] and not r.get("keep_raw", False)
    )
    return "\n".join(lines) + "\n"


def _match_exclude(domain: str, exclude: set[str]) -> bool:
    """判断域名是否命中排除列表（域名本身或其任一父域在列表中）。"""
    if domain in exclude:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts)):
        if ".".join(parts[i:]) in exclude:
            return True
    return False


def _intersects_blacklist(domain: str, black: set[str]) -> bool:
    """判断域名是否与黑名单有交集（域名本身或其任一父域在黑名单中）。

    有交集说明该域名确实被黑名单拦截，白名单放行才有修复误拦的意义；
    无交集的浏览器例外规则在 DNS 层无实际作用，应剔除。
    """
    if not black:
        return True
    if domain in black:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts)):
        if ".".join(parts[i:]) in black:
            return True
    return False


def _keep_whitelist_rule(
    domain: str,
    black: set[str],
    necessary: set[str],
    exclude: set[str],
) -> bool:
    """判断一条白名单规则是否保留。

    保留条件（全部满足）：
    - 该域名确实被黑名单拦截（与黑名单有交集，放行才有修复误拦意义）；
    - 命中「必要服务放行清单」（域名本身或其父域在 necessary 中）；
    - 未命中广告网络/追踪联盟排除列表（exclude）。
    """
    if not domain:
        return False
    if not _intersects_blacklist(domain, black):
        return False
    if _match_exclude(domain, exclude):
        return False
    if domain in necessary:
        return True
    parts = domain.split(".")
    for i in range(1, len(parts)):
        if ".".join(parts[i:]) in necessary:
            return True
    return False


def generate_whitelist(
    records: list[dict[str, Any]],
    homepage: str,
    exclude_domains: set[str] | None = None,
    black_domains: set[str] | None = None,
    necessary_domains: set[str] | None = None,
) -> str:
    """白名单：AdGuard 例外语法 @@||domain^；keep_raw 规则原样保留。

    策略（DNS 层语义）：
    - 只保留「必要服务」放行 —— 域名（或其父域）命中 necessary_domains 清单，
      且该域名确实被黑名单拦截（与黑名单有交集），放行以修复误拦。
    - 命中广告网络/追踪联盟（exclude_domains）的规则一律剔除，
      避免在 DNS 层放行广告域名解析。
    - 其余浏览器例外规则（非必要服务）直接剔除，避免放行广告。
    """
    exclude = exclude_domains or set()
    black = black_domains or set()
    necessary = necessary_domains or set()
    lines = [_header("whitelist", "白名单（放行）", homepage)]
    for r in records:
        domain = r.get("domain", "")
        if r.get("keep_raw", False):
            if not domain:
                domain = RuleClassifier._extract_host(r["raw"])
            if domain and _keep_whitelist_rule(domain, black, necessary, exclude):
                lines.append(r["raw"])
            continue
        if not domain:
            continue
        if _keep_whitelist_rule(domain, black, necessary, exclude):
            lines.append("@@||" + domain + "^")
    return "\n".join(lines) + "\n"


GENERATORS = {
    "hosts": generate_hosts,
    "adblock": generate_adblock,
    "blacklist": generate_blacklist,
    "whitelist": generate_whitelist,
}


def generate_outputs(
    merged: dict[str, list[dict[str, Any]]],
    settings: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    """生成全部产物，返回 {file_name: content}。"""
    homepage = "https://github.com/" + "/".join(
        x for x in resolve_repo_name(settings) if x
    )
    black = merged.get("blacklist", [])
    white = merged.get("whitelist", [])

    by_format = {
        "hosts": black,
        "adblock": black,
        "blacklist": black,
        "whitelist": white,
    }

    outputs: dict[str, str] = {}
    black_domains: set[str] = set()
    for r in black:
        d = r.get("domain", "")
        if d:
            black_domains.add(d.lower())
    for file_conf in settings["output"]["files"]:
        name = file_conf["name"]
        fmt = file_conf["format"]
        gen = GENERATORS.get(fmt)
        if not gen:
            print(f"[generate] 跳过未知格式: {fmt}")
            continue
        records = by_format.get(fmt, [])
        if fmt == "whitelist":
            exclude = set(settings.get("whitelist_exclude_domains", []))
            necessary = set(settings.get("whitelist_necessary_domains", []))
            outputs[name] = gen(records, homepage, exclude_domains=exclude,
                                black_domains=black_domains,
                                necessary_domains=necessary)
        else:
            outputs[name] = gen(records, homepage)

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        _write_file(output_dir / name, content)
        print(f"[generate] 写入 {output_dir / name} ({len(content.splitlines())} 行)")
    return outputs


def generate_manifest(
    outputs: dict[str, str],
    settings: dict[str, Any],
    output_dir: Path,
) -> str:
    """生成订阅源链接清单（raw.githubusercontent + jsDelivr CDN）。

    返回 manifest JSON 文本。
    """
    import json

    owner, repo = resolve_repo_name(settings)
    branch = settings["repository"].get("branch", "main")
    rel_dir = settings["repository"].get("output_dir_in_repo", "data/output")

    entries = []
    for cdn in settings.get("cdn", []):
        template = cdn["url_template"]
        for name, content in outputs.items():
            path = f"{rel_dir}/{name}"
            url = template.format(owner=owner, repo=repo, branch=branch, path=path)
            entries.append(
                {
                    "file": name,
                    "lines": len(content.splitlines()),
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "cdn": cdn["name"],
                    "url": url,
                }
            )

    manifest = {
        "generated_at": _beijing_now().isoformat(timespec="seconds"),
        "repository": {"owner": owner, "repo": repo, "branch": branch},
        "links": entries,
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    _write_file(output_dir / "manifest.json", text)
    print(f"[generate] 写入 {output_dir / 'manifest.json'}")
    return text
