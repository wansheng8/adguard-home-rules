"""步骤① 采集：从 sources.yaml 配置的源拉取规则内容，带超时与重试。"""
from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT


class FetchError(Exception):
    """采集失败。"""


def _fetch_url(url: str, timeout: float, retries: int = 3) -> bytes:
    """带重试的 URL 下载。"""
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "adguard-sync/0.1 (+https://github.com/)",
                    "Accept": "text/plain,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as err:
            last_err = err
            if attempt < retries:
                backoff = 3 * (attempt + 1)
                print(f"[collect] 重试 {url} (第 {attempt + 1} 次, {backoff}s 后)")
                time.sleep(backoff)
    raise FetchError(f"采集失败 {url}: {last_err}")


def _cache_filename(kind: str, idx: int, url: str) -> str:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    return f"{kind}_{idx}_{digest}.txt"


def fetch_source(source: dict[str, Any], raw_dir: Path, kind: str = "", idx: int = 0) -> list[str]:
    """采集单个源，返回按行拆分的文本；失败时返回空并打印告警。

    支持 file:// 前缀用于本地调试。
    """
    url = source.get("url", "")
    timeout = float(source.get("timeout", 15))
    if not url:
        print(f"[collect] 跳过空 URL 的源: {source.get('note', '')}")
        return []

    try:
        if url.startswith("file://"):
            path = Path(url[7:])
            if not path.is_absolute():
                path = REPO_ROOT / path
            raw = path.read_bytes()
        else:
            raw = _fetch_url(url, timeout)
    except FetchError as err:
        print(f"[collect] 警告: {err}")
        return []

    text = raw.decode("utf-8", errors="replace")
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache_file = raw_dir / _cache_filename(kind, idx, url)
    try:
        cache_file.write_text(text, encoding="utf-8")
    except OSError as err:
        print(f"[collect] 警告: 缓存写入失败 {cache_file}: {err}")
    return text.splitlines()


def collect_all(sources: dict[str, Any], raw_dir: Path) -> dict[str, list[str]]:
    """采集全部启用源。返回 {source_index: lines}，source_index 为列表内序号。"""
    result: dict[str, list[str]] = {}
    for kind in ("blacklist", "whitelist"):
        for idx, src in enumerate(sources.get(kind, [])):
            key = f"{kind}[{idx}]"
            result[key] = fetch_source(src, raw_dir, kind, idx)
            print(
                f"[collect] {kind}[{idx}] {src.get('note', src.get('url'))} "
                f"-> {len(result[key])} 行"
            )
    return result


def load_cached(sources: dict[str, Any], raw_dir: Path) -> dict[str, list[str]]:
    """从缓存目录加载上次采集的原始数据（离线调试用）。"""
    result: dict[str, list[str]] = {}
    for kind in ("blacklist", "whitelist"):
        for idx, src in enumerate(sources.get(kind, [])):
            key = f"{kind}[{idx}]"
            cache_file = raw_dir / _cache_filename(kind, idx, src.get("url", ""))
            if not cache_file.exists():
                print(f"[collect] 警告: 缓存缺失 {cache_file}")
                result[key] = []
                continue
            result[key] = cache_file.read_text(encoding="utf-8").splitlines()
    return result
