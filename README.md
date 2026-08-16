# AdGuard Home 规则聚合订阅

自动聚合多个开源黑白名单，经语法校验、分类、去重后生成 AdGuard Home 可订阅的规则文件，并每 8 小时按北京时间自动更新。

## 订阅链接

### `hosts.txt`

| CDN | 订阅链接 |
| --- | --- |
| raw.githubusercontent.com | `https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/hosts.txt` |
| cdn.jsdelivr.net | `https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/hosts.txt` |

### `adblock.txt`

| CDN | 订阅链接 |
| --- | --- |
| raw.githubusercontent.com | `https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/adblock.txt` |
| cdn.jsdelivr.net | `https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/adblock.txt` |

### `blacklist.txt`

| CDN | 订阅链接 |
| --- | --- |
| raw.githubusercontent.com | `https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/blacklist.txt` |
| cdn.jsdelivr.net | `https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/blacklist.txt` |

### `whitelist.txt`

| CDN | 订阅链接 |
| --- | --- |
| raw.githubusercontent.com | `https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/whitelist.txt` |
| cdn.jsdelivr.net | `https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/whitelist.txt` |

## 使用方式（AdGuard Home）

在 AdGuard Home 的「过滤器 → DNS 拦截清单」中添加上述链接即可订阅：

1. 打开 AdGuard Home 管理面板
2. 进入 **过滤器** → **DNS 拦截清单** → **添加过滤器**
3. 粘贴上表中的任一订阅链接（推荐 `hosts.txt` 或 `adblock.txt`）
4. 若需放行误拦域名，同时订阅 `whitelist.txt`

> 提示：国内环境可优先选用 `cdn.jsdelivr.net` 加速链接。

## 规则统计

| 分类 | 黑名单 | 白名单 |
| --- | ---: | ---: |
| advertising | 159598 | 200 |
| tracking | 25630 | 19 |
| social | 146 | 0 |
| adult | 897 | 0 |
| phishing | 53 | 0 |
| malware | 672 | 0 |
| other | 80340 | 263 |
| **合计** | **267336** | **482** |

## 更新信息

- 时区：北京时间 (Asia/Shanghai)
- 更新频率：每 8 小时自动同步一次（GitHub Actions 定时任务）
- 最近更新时间：2026-08-16 10:55:13

[GitHub 仓库](https://github.com/wansheng8/adguard-home-rules)
