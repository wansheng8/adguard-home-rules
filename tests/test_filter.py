"""语法过滤模块单元测试 —— 基于 AdGuard Home 完整语法清单。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adguard_sync.config import load_syntax
from adguard_sync.steps.filter import RuleClassifier


def setup_classifier():
    return RuleClassifier(load_syntax())


def test_domain_rule_basic():
    """||domain^ 匹配域名及其所有子域。"""
    c = setup_classifier()
    rec = c.classify("||doubleclick.net^")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "doubleclick.net"
    assert rec["output"] == "adblock"


def test_domain_rule_no_caret():
    """||domain 省略 ^ 同样有效。"""
    c = setup_classifier()
    rec = c.classify("||ads.example.com")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "ads.example.com"


def test_url_prefix_rule():
    """|https://domain^ 地址开头写法，DNS 层提取域名。"""
    c = setup_classifier()
    rec = c.classify("|https://example.com^")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "example.com"


def test_wildcard_rule():
    """||*.example.com^ 通配符，提取基础域名并原样保留。"""
    c = setup_classifier()
    rec = c.classify("||*.tracker.com^")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "tracker.com"
    assert rec["keep_raw"] is True


def test_whitelist_rule():
    """@@||allowed.example.com^ 白名单，优先级高于拦截。"""
    c = setup_classifier()
    rec = c.classify("@@||allowed.example.com^")
    assert rec["action"] == "whitelist"
    assert rec["domain"] == "allowed.example.com"


def test_whitelist_rule_no_caret():
    """@@||sub.example.com 省略 ^。"""
    c = setup_classifier()
    rec = c.classify("@@||sub.example.com")
    assert rec["action"] == "whitelist"
    assert rec["domain"] == "sub.example.com"


def test_whitelist_single_bar():
    """@@|cdn.taboola.com^| 单竖线白名单变体（AdGuard DNS filter 常见格式）。"""
    c = setup_classifier()
    rec = c.classify("@@|cdn.taboola.com^|")
    assert rec["action"] == "whitelist"
    assert rec["domain"] == "cdn.taboola.com"


def test_hosts_rule():
    """0.0.0.0 ads.example.com hosts 格式。"""
    c = setup_classifier()
    rec = c.classify("0.0.0.0 ads.example.com")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "ads.example.com"
    assert rec["output"] == "hosts"


def test_hosts_rule_127():
    """127.0.0.1 tracker.example.com。"""
    c = setup_classifier()
    rec = c.classify("127.0.0.1 tracker.example.com")
    assert rec["domain"] == "tracker.example.com"


def test_hosts_reversed():
    """domain IP 反写格式同样识别。"""
    c = setup_classifier()
    rec = c.classify("ads.example.com 0.0.0.0")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "ads.example.com"
    assert rec["output"] == "hosts"


def test_regex_rule():
    """/^ads\d*\.example\.com$/ 正则规则，原样保留。"""
    c = setup_classifier()
    rec = c.classify("/^ads\\d*\\.example\\.com$/")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == ""
    assert rec["keep_raw"] is True
    assert rec["raw"].startswith("/")


def test_comment_adblock_style():
    """! 注释。"""
    c = setup_classifier()
    assert c.classify("! 这是一条注释") is None


def test_comment_hosts_style():
    """# 注释。"""
    c = setup_classifier()
    assert c.classify("# 这也是一条注释") is None


def test_modifier_important():
    """||example.com^$important 支持，提取域名。"""
    c = setup_classifier()
    rec = c.classify("||example.com^$important")
    assert rec["action"] == "blacklist"
    assert rec["domain"] == "example.com"


def test_modifier_denyallow():
    """$denyallow= 排除子域，提取主域。"""
    c = setup_classifier()
    rec = c.classify("||example.com^$denyallow=sub.example.com")
    assert rec["domain"] == "example.com"


def test_modifier_denyallow_multi():
    """$denyallow= 多个排除用 | 分隔。"""
    c = setup_classifier()
    rec = c.classify("||example.com^$denyallow=sub1.example.com|sub2.example.com")
    assert rec["domain"] == "example.com"


def test_modifier_dnstype():
    """$dnstype=A 只拦截特定查询类型。"""
    c = setup_classifier()
    rec = c.classify("||example.com^$dnstype=A")
    assert rec["domain"] == "example.com"
    rec = c.classify("||example.com^$dnstype=A|AAAA")
    assert rec["domain"] == "example.com"


def test_modifier_client():
    """$client=IP/CIDR/MAC 客户端限制。"""
    c = setup_classifier()
    assert c.classify("||example.com^$client=192.168.1.100")["domain"] == "example.com"
    assert c.classify("||example.com^$client=192.168.1.0/24")["domain"] == "example.com"
    assert c.classify("||example.com^$client=aa:bb:cc:dd:ee:ff")["domain"] == "example.com"


def test_modifier_ctag():
    """$ctag= 客户端标签。"""
    c = setup_classifier()
    rec = c.classify("||example.com^$ctag=work")
    assert rec["domain"] == "example.com"


def test_modifier_dnsrewrite():
    """$dnsrewrite= DNS 重写。"""
    c = setup_classifier()
    assert c.classify("||example.com^$dnsrewrite=1.2.3.4")["domain"] == "example.com"
    assert c.classify("||example.com^$dnsrewrite=NXDOMAIN")["domain"] == "example.com"


def test_unsupported_path():
    """路径过滤 ||example.com/banner/* 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("||example.com/banner/*") is None


def test_unsupported_elemhide():
    """元素隐藏 ##.ad-banner 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("##.ad-banner") is None


def test_unsupported_elemhide_exception():
    """元素隐藏例外 #@#.ad 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("#@#.ad") is None


def test_unsupported_script_injection():
    """脚本注入 ##+js(...) 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("##+js(no-setInterval-if, /\\.com/)") is None


def test_unsupported_style_injection():
    """样式注入 ##+style(...) 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("example.com##+style(background: red)") is None


def test_unsupported_resource_modifier():
    """资源类型修饰符 $script / $third-party 不支持 → 忽略。"""
    c = setup_classifier()
    assert c.classify("||example.com^$script") is None
    assert c.classify("||example.com^$script,third-party") is None


def test_unsupported_browser_modifier():
    """$redirect / $replace / $csp / $header 浏览器专有 → 忽略。"""
    c = setup_classifier()
    assert c.classify("||example.com^$redirect=noop.js") is None
    assert c.classify("||example.com^$replace=/a/b") is None
    assert c.classify("||example.com^$csp=script-src *") is None
    assert c.classify("||example.com^$header=set-cookie:x") is None


def test_empty_line():
    c = setup_classifier()
    assert c.classify("") is None
    assert c.classify("   ") is None


def test_reserved_host_ignored():
    c = setup_classifier()
    assert c.classify("localhost") is None
    assert c.classify("0.0.0.0 localhost") is None


def test_invalid_domain_rejected():
    c = setup_classifier()
    assert c.classify("0.0.0.0 -bad-") is None
    assert c.classify("0.0.0.0") is None


def test_category_guess():
    c = setup_classifier()
    rec = c.classify("0.0.0.0 ads.doubleclick.net")
    assert rec["category"] == "advertising"
