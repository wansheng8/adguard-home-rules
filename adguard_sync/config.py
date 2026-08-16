"""配置加载模块：读取 sources.yaml / syntax.yaml / settings.yaml。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式错误（应为 YAML 映射）: {path}")
    return data


def load_sources(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    """加载采集源配置，仅返回 enabled 的条目。"""
    sources = _load_yaml(config_dir / "sources.yaml")
    for key in ("blacklist", "whitelist"):
        items = sources.get(key, [])
        sources[key] = [i for i in items if i.get("enabled", True)]
    return sources


def load_syntax(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    """加载规则语法定义。"""
    return _load_yaml(config_dir / "syntax.yaml")


def load_settings(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    """加载全局设置。"""
    return _load_yaml(config_dir / "settings.yaml")


def resolve_repo_name(settings: dict[str, Any]) -> tuple[str, str]:
    """探测仓库 owner/repo：优先配置，其次 git remote。"""
    owner = settings.get("repository", {}).get("owner", "")
    repo = settings.get("repository", {}).get("repo", "")
    if owner and repo:
        return owner, repo

    try:
        import subprocess

        out = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        # 支持 https://github.com/owner/repo.git 与 git@github.com:owner/repo.git
        out = out.replace(".git", "").rstrip("/")
        if "github.com/" in out:
            head = out.split("github.com/", 1)[1]
        elif "github.com:" in out:
            head = out.split("github.com:", 1)[1]
        else:
            head = out
        parts = head.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    except Exception:
        pass
    return "", ""
