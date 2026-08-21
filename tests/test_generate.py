"""generate 步骤测试：白名单广告网络域名剔除。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adguard_sync.steps.generate import generate_whitelist, _match_exclude


def _record(domain: str, raw: str = "", keep_raw: bool = False) -> dict:
    return {
        "domain": domain,
        "raw": raw or ("@@||" + domain + "^"),
        "keep_raw": keep_raw,
    }


def test_match_exclude_exact():
    """域名本身命中排除列表。"""
    exclude = {"adsterra.com"}
    assert _match_exclude("adsterra.com", exclude) is True
    assert _match_exclude("ads.adsterra.com", exclude) is True
    assert _match_exclude("example.com", exclude) is False


def test_match_exclude_subdomain():
    """子域命中父域排除项。"""
    exclude = {"doubleclick.net"}
    assert _match_exclude("pagead.l.doubleclick.net", exclude) is True
    assert _match_exclude("www3.doubleclick.net", exclude) is True
    assert _match_exclude("doubleclick.net", exclude) is True


def test_whitelist_excludes_ad_network():
    """白名单剔除广告网络域名。"""
    records = [
        _record("adsterra.com"),
        _record("cdn.taboola.com"),
        _record("speedtest.net"),
        _record("battle.net"),
    ]
    out = generate_whitelist(records, "https://github.com/x/y",
                             exclude_domains={"adsterra.com", "taboola.com"})
    assert "@@||adsterra.com^" not in out
    assert "@@||cdn.taboola.com^" not in out
    assert "@@||speedtest.net^" in out
    assert "@@||battle.net^" in out


def test_whitelist_keeps_necessary():
    """必要服务白名单保留。"""
    records = [_record("speedtest.net"), _record("m.jd.com"), _record("360.cn")]
    out = generate_whitelist(records, "https://github.com/x/y",
                             exclude_domains={"adsterra.com"})
    assert "@@||speedtest.net^" in out
    assert "@@||m.jd.com^" in out
    assert "@@||360.cn^" in out


def test_whitelist_keep_raw_excluded():
    """keep_raw 通配符白名单规则同样被剔除。"""
    records = [_record("ay.delivery", raw="@@||*.ay.delivery", keep_raw=True)]
    out = generate_whitelist(records, "https://github.com/x/y",
                             exclude_domains={"ay.delivery"})
    assert "@@||*.ay.delivery" not in out


def test_whitelist_keep_raw_kept():
    """keep_raw 非广告白名单规则保留。"""
    records = [_record("speedtest.net", raw="@@||*.speedtest.net^", keep_raw=True)]
    out = generate_whitelist(records, "https://github.com/x/y",
                             exclude_domains={"adsterra.com"})
    assert "@@||*.speedtest.net^" in out
