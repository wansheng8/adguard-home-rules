"""流水线编排：串联 采集→清洗→过滤→分类→去重→合并→生成→README。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from . import steps
from .config import REPO_ROOT, load_settings, load_sources, load_syntax

# 让 steps 包可被导入（作为命名空间目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _import_step(name: str):
    import importlib

    mod = importlib.import_module(f".steps.{name}", __package__)
    return mod


def run_pipeline(no_fetch: bool = False) -> dict[str, Any]:
    """执行完整流水线，返回各步骤统计信息。"""
    settings = load_settings()
    sources = load_sources()
    syntax = load_syntax()

    raw_dir = REPO_ROOT / "data" / "raw"
    cache_dir = REPO_ROOT / "data" / "cache"
    out_dir = REPO_ROOT / settings["output"]["dir"]

    stats: dict[str, Any] = {}

    # ① 采集
    collect = _import_step("collect")
    if no_fetch:
        fetched = collect.load_cached(sources, raw_dir)
        print(f"[pipeline] 使用缓存原始数据（{len(fetched)} 个源）")
    else:
        fetched = collect.collect_all(sources, raw_dir)
    stats["sources"] = {k: len(v) for k, v in fetched.items()}

    # ② 清洗
    clean = _import_step("clean")
    cleaned: dict[str, list[str]] = {k: clean.clean_lines(v) for k, v in fetched.items()}
    stats["cleaned"] = {k: len(v) for k, v in cleaned.items()}

    # ③ 语法过滤
    filter_mod = _import_step("filter")
    all_records: list[dict[str, Any]] = []
    for kind in ("blacklist", "whitelist"):
        for idx, src in enumerate(sources.get(kind, [])):
            key = f"{kind}[{idx}]"
            src_category = src.get("category", "other")
            recs = filter_mod.filter_rules(
                cleaned.get(key, []),
                syntax,
                source=key,
            )
            for r in recs:
                r["source_kind"] = kind
                r["source_category"] = src_category
            all_records.extend(recs)
    stats["filtered"] = {
        "blacklist": sum(1 for r in all_records if r["action"] == "blacklist"),
        "whitelist": sum(1 for r in all_records if r["action"] == "whitelist"),
        "ignored": sum(1 for r in []),  # 占位，忽略行已在 filter 中丢弃
    }

    # ④ 分类
    classify = _import_step("classify")
    all_records = classify.classify_records(all_records)

    # ⑤ 去重
    dedupe = _import_step("dedupe")
    deduped = dedupe.dedupe_records(all_records)
    stats["deduped"] = len(deduped)

    # ⑥ 合并
    merge = _import_step("merge")
    merged = merge.split_by_action(deduped)
    stats["merged"] = {k: len(v) for k, v in merged.items()}

    # ⑦ 生成
    generate = _import_step("generate")
    outputs = generate.generate_outputs(merged, settings, out_dir)
    generate.generate_manifest(outputs, settings, out_dir)
    stats["outputs"] = {k: len(v.splitlines()) for k, v in outputs.items()}

    # ⑧ 构建 README
    readme = _import_step("readme")
    content = readme.build_readme(merged, settings, stats)
    readme.write_readme(content)
    stats["readme"] = len(content.splitlines())

    return stats


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AdGuard 规则聚合流水线")
    parser.add_argument("--no-fetch", action="store_true", help="使用缓存原始数据，不联网采集")
    args = parser.parse_args()

    stats = run_pipeline(no_fetch=args.no_fetch)
    print("\n[pipeline] 完成。统计：")
    import json

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
