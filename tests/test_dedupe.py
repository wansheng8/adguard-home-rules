"""去重模块单元测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adguard_sync.steps.dedupe import dedupe_records


def _rec(domain, action, raw=None):
    return {
        "raw": raw or domain,
        "domain": domain,
        "action": action,
    }


def test_dedupe_exact():
    recs = [_rec("a.example.com", "blacklist"), _rec("a.example.com", "blacklist")]
    out = dedupe_records(recs)
    assert len(out) == 1


def test_blacklist_wins_over_whitelist():
    """DNS 层广告拦截优先：同一域名黑白名单冲突时保留黑名单。"""
    recs = [
        _rec("x.example.com", "blacklist"),
        _rec("x.example.com", "whitelist"),
    ]
    out = dedupe_records(recs)
    assert len(out) == 1
    assert out[0]["action"] == "blacklist"


def test_blacklist_wins_whitelist_first():
    """即使白名单先出现，黑名单仍优先。"""
    recs = [
        _rec("x.example.com", "whitelist"),
        _rec("x.example.com", "blacklist"),
    ]
    out = dedupe_records(recs)
    assert len(out) == 1
    assert out[0]["action"] == "blacklist"


def test_blacklist_kept_when_no_conflict():
    recs = [
        _rec("a.example.com", "blacklist"),
        _rec("b.example.com", "whitelist"),
    ]
    out = dedupe_records(recs)
    assert len(out) == 2


def test_case_insensitive():
    recs = [_rec("A.Example.COM", "blacklist"), _rec("a.example.com", "blacklist")]
    out = dedupe_records(recs)
    assert len(out) == 1
