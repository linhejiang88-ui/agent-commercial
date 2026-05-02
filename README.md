# 软件生态市场分析文档工作区

本目录用于沉淀 `2026 年软件开发、AI Agent 外包、AI 咨询服务、接单平台与渠道岗位数据` 的研究文档、图表资产和抓取证据。

当前核心结论：**3 人技术团队在 2026 年最值得优先布局的方向，不是纯软件人天外包，而是 `AI 咨询 + AI Agent 实施 + 托管运营` 的组合型服务。**

## 1. 核心文档

| 文档 | 定位 | 说明 |
| --- | --- | --- |
| [`2026年软件及AI-Agent外包及咨询市场分析报告（插图版）.md`](2026年软件及AI-Agent外包及咨询市场分析报告（插图版）.md) | 主要文档 | 当前推荐优先阅读版本，已插入 9 张 SVG 图，并在文末附上渠道统计、截图目录和四平台分析附件。 |
| [`2025-2026四大接单平台数据分析报告.md`](2025-2026四大接单平台数据分析报告.md) | 四平台分析 | Upwork、Fiverr、程序员客栈、猪八戒的平台模式、费用、供需强度和适合方向分析。 |

## 2. 渠道 Job 数据与截图

| 文件 / 目录 | 用途 |
| --- | --- |
| [`渠道Job岗位数Scraping统计-CDP-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-CDP-2026-05-02.md) | 主要渠道岗位 / 项目数量统计表，基于 Chrome CDP 复用真实浏览器状态抓取。 |
| [`渠道Job调研/screenshots/`](渠道Job调研/screenshots/) | 渠道 Job 核心页面截图目录，统计表中的截图链接均指向这里。 |
| [`渠道Job调研/data/channel_job_scrape_cdp_2026-05-02.json`](渠道Job调研/data/channel_job_scrape_cdp_2026-05-02.json) | CDP 抓取的结构化结果，便于后续二次处理。 |
| [`渠道Job搜索清单.md`](渠道Job调研/渠道Job搜索清单.md) | 平台、关键词、筛选条件和统计口径清单。 |
| [`Chrome-CDP抓取使用说明.md`](渠道Job调研/Chrome-CDP抓取使用说明.md) | 如何启动带 CDP 端口的 Chrome、复用登录态并运行抓取脚本。 |
| [`scripts/scrape_channel_jobs.py`](渠道Job调研/scripts/scrape_channel_jobs.py) | 渠道岗位数抓取脚本，支持 `--cdp-url`、`--platform`、`--missing-counts-from`。 |

补充过程文件：

- [`渠道Job岗位数Scraping统计-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-2026-05-02.md)：普通浏览器抓取结果。
- [`渠道Job岗位数Scraping统计-CDP测试-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-CDP测试-2026-05-02.md)：CDP 小样本测试结果。
- [`渠道Job岗位数Scraping统计-CDP补抓未取数-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-CDP补抓未取数-2026-05-02.md)：未取数记录补抓结果。
- [`渠道Job岗位数Scraping统计-CDP补抓Upwork-Fiverr-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-CDP补抓Upwork-Fiverr-2026-05-02.md)：Upwork / Fiverr 失败项补抓结果。
- [`渠道Job岗位数统计-2026-05-02.md`](渠道Job调研/渠道Job岗位数统计-2026-05-02.md)：早期公开页 / 索引页统计版本，用于对照。

## 3. 图表与素材

| 目录 / 文件 | 用途 |
| --- | --- |
| [`images/`](images/) | 报告图片资产目录，当前主要包含 SVG 图表。 |
| [`报告插图规划.md`](报告插图规划.md) | 插图规划文件，列出推荐插图模块、图表类型、位置和数据来源。 |

已生成 SVG 图表：

| 图编号 | 文件 | 用途 |
| --- | --- | --- |
| 图 1 | [`images/fig-01-opportunity-ranking.svg`](images/fig-01-opportunity-ranking.svg) | 机会排序图。 |
| 图 2 | [`images/fig-02-market-size-cagr.svg`](images/fig-02-market-size-cagr.svg) | 软件外包、AI Agent、AI 咨询市场规模和 CAGR 对比。 |
| 图 3 | [`images/fig-03-china-ito-bpo-kpo.svg`](images/fig-03-china-ito-bpo-kpo.svg) | 中国 ITO / BPO / KPO 执行额和同比增速对比。 |
| 图 4 | [`images/fig-04-outsourcing-fusion.svg`](images/fig-04-outsourcing-fusion.svg) | ITO / BPO / KPO 与 AI Agent、AI 咨询融合结构。 |
| 图 5 | [`images/fig-05-channel-funnel.svg`](images/fig-05-channel-funnel.svg) | 获客渠道角色分工。 |
| 图 6 | [`images/fig-06-ai-consulting-delivery-chain.svg`](images/fig-06-ai-consulting-delivery-chain.svg) | AI 咨询服务交付链路。 |
| 图 7 | [`images/fig-07-product-profit-comparison.svg`](images/fig-07-product-profit-comparison.svg) | 产品量级、交付周期和毛利率对比。 |
| 图 8 | [`images/fig-08-ai-coding-impact.svg`](images/fig-08-ai-coding-impact.svg) | AI Coding 对 ITO / BPO / KPO 的影响。 |
| 图 9 | [`images/fig-09-12-month-roadmap.svg`](images/fig-09-12-month-roadmap.svg) | 3 人团队 12 个月执行路线图。 |

## 4. 辅助文档

| 文档 | 用途 |
| --- | --- |
| [`如何接单.md`](如何接单.md) | 接单方法、渠道动作和执行建议。 |
| [`AGENTS.md`](AGENTS.md) | 本工作区写作、验证和维护规则。 |

## 5. 推荐阅读顺序

1. 先读 [`2026年软件及AI-Agent外包及咨询市场分析报告（插图版）.md`](2026年软件及AI-Agent外包及咨询市场分析报告（插图版）.md)，快速理解核心结论和图表。
2. 再读 [`2025-2026四大接单平台数据分析报告.md`](2025-2026四大接单平台数据分析报告.md)，理解 Upwork、Fiverr、程序员客栈、猪八戒的渠道差异。
3. 查看 [`渠道Job岗位数Scraping统计-CDP-2026-05-02.md`](渠道Job调研/渠道Job岗位数Scraping统计-CDP-2026-05-02.md) 和 [`渠道Job调研/screenshots/`](渠道Job调研/screenshots/)，核对平台关键词数量和截图证据。
4. 如需复跑或补抓，按 [`Chrome-CDP抓取使用说明.md`](渠道Job调研/Chrome-CDP抓取使用说明.md) 操作。
5. 如需调整图表或扩展正文，再参考 [`报告插图规划.md`](报告插图规划.md)。

## 6. 本地校验命令

```bash
rg -n "^## |^### " .
rg -n "TODO|待补充|TBD" .
for f in images/*.svg; do xmllint --noout "$f" || exit 1; done
```

## 7. 维护约定

- 主报告统一维护插图版，不在根目录保留重复草稿。
- 渠道岗位数优先采用 CDP 统计报告；普通抓取和补抓文件只作为过程证据。
- 渠道 Job 新增截图统一放入 `渠道Job调研/screenshots/`；报告插图和其他主题图片放入 `images/<topic>/` 或 `images/`。
- 不将 `.venv-*`、`.DS_Store`、`__pycache__/` 等本地生成文件纳入版本管理。
