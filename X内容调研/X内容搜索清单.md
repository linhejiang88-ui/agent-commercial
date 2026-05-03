# X 内容搜索清单

## 统一抓取规则

- 只抓取公开 Posts，不抓取私信、受保护账号或无法公开复核的内容。
- 当前主流程使用 Chrome CDP 低频打开 X Top 搜索页；不点赞、关注、评论、转发，不做深度翻页。
- 如使用官方 API，默认时间窗口为最近 7 天；历史趋势需要切换到 X API Full-Archive Search 权限。
- API 模式下先用 Recent Counts 判断关键词热度，再用 Recent Search 抓取样本。
- 报告中只使用归纳后的市场信号；原文链接、截图和 JSON 作为证据留存。
- 对营销号、搬运内容和无来源夸张数据标记为低价值或噪声。

## CDP 商业化查询

| 主题 | 查询语句 | 用途 |
| --- | --- | --- |
| AI 自动化服务 | `("AI automation" OR "n8n" OR "Make.com") ("clients" OR "revenue" OR "MRR" OR "$") ("workflow" OR "agency" OR "case study") -giveaway -airdrop -hiring -jobs` | 观察自动化服务、客户交付和收入复盘。 |
| AI Agent 产品 | `("AI agent" OR "AI agents") ("I built" OR "I launched" OR "revenue" OR "MRR" OR "$") -giveaway -airdrop -hiring -jobs` | 观察 Agent 产品化和收入信号。 |
| AI 微型 SaaS | `("AI SaaS" OR "micro SaaS") ("MRR" OR "revenue" OR "users" OR "launched" OR "$") -giveaway -airdrop -hiring -jobs` | 观察微型 SaaS、MRR、用户数和产品 listing。 |
| AI 模板 / Prompt | `("AI templates" OR "AI prompts" OR "prompt pack") ("sold" OR "revenue" OR "customers" OR "$") -giveaway -airdrop -hiring -jobs` | 观察低价内容产品和交付资产复用。 |
| AI Newsletter | `("AI newsletter" OR "newsletter about AI") ("revenue" OR "sponsors" OR "subscribers" OR "MRR" OR "$") -giveaway -airdrop -hiring -jobs` | 观察 Newsletter、赞助和订阅收入。 |
| 中文 AI 自动化 | `("AI自动化" OR "n8n" OR "工作流") ("接单" OR "客户" OR "收入" OR "报价" OR "复盘") -抽奖 -空投 -招聘` | 观察中文语境下的自动化接单和变现复盘。 |

完整扩展查询见 [`data/x_ai_money_queries_expanded_2026-05-03.json`](data/x_ai_money_queries_expanded_2026-05-03.json)。

## API 默认查询

| 主题 | 查询语句 | 用途 |
| --- | --- | --- |
| AI Agent | `"AI agent" ("freelancer" OR "agency" OR "consulting" OR "automation") lang:en -is:retweet` | 观察 AI Agent 外包、咨询、自动化供需。 |
| 自动化 | `"workflow automation" ("client" OR "business" OR "agency") lang:en -is:retweet` | 观察企业流程自动化需求。 |

## 统计记录模板

| 抓取日期 | 主题 | 查询语句 | 时间窗口 | Recent Count | 抓取页数 | 有效信号数 | 高价值信号数 | 输出文件 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
|  |  |  |  |  |  |  |  |  |

## 复核口径

- `需求`：客户、业务方、创业者明确表达要解决的问题或采购意图。
- `供给`：自由职业者、Agency、工具商发布服务、案例或报价。
- `价格`：出现预算、报价、套餐、订阅费、项目金额。
- `案例`：明确描述已交付、上线、实施、迁移或优化结果。
- `工具`：出现产品、API、SDK、平台能力或集成生态。
- `痛点`：出现失败、难点、成本、流程阻塞或人工替代问题。
