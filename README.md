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

## IPv4/IPv6 配置说明

本仓库的 **adblock 与 hosts 规则对 IPv4（A）和 IPv6（AAAA）查询均生效**。
订阅后在「过滤器 → DNS 拦截清单」正常拦截两种记录，无需单独处理 IPv6。
若设备仍能加载广告，请按以下顺序排查配置层绕过：

1. **确认 DNS 走 AdGuard Home**：设备 DNS 若指向运营商/路由器，或启用了 Android「私人 DNS」等加密 DNS（DoH/DoT），请求不经过本过滤器，全部失效。
2. **AdGuard Home 监听地址**：在「设置 → DNS 设置 → 监听接口」中确保同时监听 IPv4 与 IPv6（如 `0.0.0.0` 与 `::`），否则仅 IPv6 设备（如部分手机默认 IPv6）的查询不受控。
3. **阻断方式（Blocking mode）**：在「设置 → DNS 设置」中选用 **Null IP** 或 **NXDOMAIN**。Null IP 会对 A 返回 `0.0.0.0`、对 AAAA 返回 `::`，两种记录都被拦；若误用自定义 IP 且仅填写 IPv4，AAAA 查询将放行。
4. **IPv6 上游**：若启用 IPv6 上游或路由器下发了 IPv6 DNS，确认客户端实际使用的解析服务器仍是 AdGuard Home。

## 规则统计

| 分类 | 黑名单 | 白名单 |
| --- | ---: | ---: |
| advertising | 277745 | 347 |
| tracking | 48441 | 30 |
| social | 1024 | 2 |
| adult | 2047 | 0 |
| phishing | 152 | 0 |
| malware | 1718 | 0 |
| other | 349254 | 230 |
| **合计** | **680381** | **609** |

## 更新信息

- 时区：北京时间 (Asia/Shanghai)
- 更新频率：每 8 小时自动同步一次（GitHub Actions 定时任务）
- 最近更新时间：2026-08-23 00:45:36

[GitHub 仓库](https://github.com/wansheng8/adguard-home-rules)
