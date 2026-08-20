# AdGuard Home 规则聚合订阅

自动聚合多个开源黑白名单，经语法校验、分类、去重后生成 AdGuard Home 可订阅的规则文件，并每 8 小时按北京时间自动更新。

## 订阅链接

| 过滤器类型 | 完整版 | 精简版 |
| --- | --- | --- |
| 广告过滤器 | [Github](https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/adblock.txt) | [CDN](https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/adblock.txt) |
| DNS过滤器 | [Github](https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/黑名单.txt) | [CDN](https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/黑名单.txt) |
| Host列表 | [Github](https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/hosts.txt) | [CDN](https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/hosts.txt) |
| 白名单 | [Github](https://raw.githubusercontent.com/wansheng8/adguard-home-rules/main/data/output/白名单.txt) | [CDN](https://cdn.jsdelivr.net/gh/wansheng8/adguard-home-rules@main/data/output/白名单.txt) |

## 使用方式（AdGuard Home）

在 AdGuard Home 的「过滤器 → DNS 拦截清单」中添加上表中的链接即可订阅：

1. 打开 AdGuard Home 管理面板
2. 进入 **过滤器** → **DNS 拦截清单** → **添加过滤器**
3. 粘贴上表中的订阅链接（推荐 **广告过滤器** 或 **DNS过滤器**）
4. 若需放行误拦域名，同时订阅 **白名单**

> 提示：国内环境可优先选用 `cdn.jsdelivr.net` 加速链接。

## 规则统计

| 分类 | 黑名单 | 白名单 |
| --- | ---: | ---: |
| advertising | 198179 | 300 |
| tracking | 36916 | 25 |
| social | 800 | 2 |
| adult | 1545 | 0 |
| phishing | 138 | 0 |
| malware | 1609 | 0 |
| other | 331461 | 263 |
| **合计** | **570648** | **590** |

## 更新信息

- 时区：北京时间 (Asia/Shanghai)
- 更新频率：每 8 小时自动同步一次（GitHub Actions 定时任务）
- 最近更新时间：2026-08-20 16:25:56

[GitHub 仓库](https://github.com/wansheng8/adguard-home-rules)
