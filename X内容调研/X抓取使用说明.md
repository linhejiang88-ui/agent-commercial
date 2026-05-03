# X 抓取使用说明

本文说明如何抓取 X 上的公开内容，并整理为市场研究素材。当前仓库支持两条路径：

- **无 API 路径（当前主用）：** `scripts/scrape_x_cdp.py` 连接本机已登录 Chrome CDP，低频打开 X Top 搜索页，保存可见帖子、截图和 Markdown 报告。
- **官方 API 路径（备用）：** `scripts/scrape_x_posts.py` 使用 X API Recent Search，需要 `X_BEARER_TOKEN`。

## 1. 无 API：Chrome CDP 低频采集

适用于没有 X API 权限，但已经在本机 Chrome 登录 X 的情况。采集原则：

- 只打开公开搜索页和公开帖子；
- 不抓私信、受保护账号或无法公开复核的内容；
- 不点赞、关注、评论、转发；
- 不做高频刷新、深度翻页或并发访问；
- 结果只作为市场信号，不作为统计口径。

先用独立 Chrome Profile 启动 CDP：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$PWD/.chrome-x-scrape" \
  --no-first-run
```

在该 Chrome 中登录 X，并确认能正常打开搜索页。然后从仓库根目录运行：

```bash
./.venv-scrapling/bin/python X内容调研/scripts/scrape_x_cdp.py \
  --queries X内容调研/data/x_ai_money_queries_expanded_2026-05-03.json \
  --scrolls 0 \
  --wait-ms 7000 \
  --json X内容调研/data/x_cdp_ai_money_posts_YYYY-MM-DD.json \
  --md X内容调研/X_AI赚钱分享整理-YYYY-MM-DD.md
```

输出包括：

- `X内容调研/data/x_cdp_*.json`
- `X内容调研/X_AI赚钱分享整理-*.md`
- `X内容调研/screenshots/*.png`

当前主分析报告使用的是：

- [`X_AI赚钱分享扩展分析-2026-05-03.md`](X_AI赚钱分享扩展分析-2026-05-03.md)
- [`data/x_cdp_ai_money_posts_combined_2026-05-03.json`](data/x_cdp_ai_money_posts_combined_2026-05-03.json)
- [`data/x_ai_money_queries_expanded_2026-05-03.json`](data/x_ai_money_queries_expanded_2026-05-03.json)

## 2. 有 API：Recent Search 抓取

需要 X API Bearer Token，并在当前 shell 中设置环境变量：

```bash
export X_BEARER_TOKEN="你的 Bearer Token"
```

脚本默认使用 X API Recent Search，只覆盖最近 7 天公开 Posts。官方文档：

- https://docs.x.com/x-api/posts/search/introduction
- https://docs.x.com/x-api/posts/recent-search
- https://docs.x.com/x-api/fundamentals/rate-limits

### 2.1 小样本抓取

从仓库根目录执行：

```bash
python3 X内容调研/scripts/scrape_x_posts.py search --max-pages 1
```

默认输出：

- `X内容调研/data/x_posts_raw_YYYY-MM-DD.jsonl`
- `X内容调研/data/x_posts_normalized_YYYY-MM-DD.json`
- `X内容调研/X市场信号整理-YYYY-MM-DD.md`

### 2.2 指定时间窗口

```bash
python3 X内容调研/scripts/scrape_x_posts.py search \
  --start-time 2026-04-26 \
  --end-time 2026-05-03 \
  --max-pages 2
```

Recent Search 的时间窗口不能超过当前权限支持范围。普通 Recent Search 通常用于最近 7 天。

### 2.3 自定义查询

```bash
python3 X内容调研/scripts/scrape_x_posts.py search \
  --query '"AI consulting" ("client" OR "agency") lang:en -is:retweet' \
  --query '"AI Agent" ("budget" OR "pricing") lang:en -is:retweet' \
  --max-pages 1
```

如需长期维护多组查询，可创建 JSON 文件：

```json
[
  {
    "name": "AI 咨询报价",
    "query": "\"AI consulting\" (\"budget\" OR \"pricing\") lang:en -is:retweet",
    "topic": "价格"
  }
]
```

然后运行：

```bash
python3 X内容调研/scripts/scrape_x_posts.py search --queries X内容调研/data/x_queries.json
```

### 2.4 API 结果截图留证

高价值帖建议保存截图。截图子命令依赖 Playwright，建议使用仓库已有的 `.venv-scrapling` 环境。先用独立 Chrome Profile 启动 CDP：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$PWD/.chrome-x-scrape" \
  --no-first-run
```

在该 Chrome 中登录 X 并确认能打开帖子链接，然后运行：

```bash
./.venv-scrapling/bin/python X内容调研/scripts/scrape_x_posts.py screenshot \
  --input X内容调研/data/x_posts_normalized_YYYY-MM-DD.json \
  --cdp-url http://127.0.0.1:9222 \
  --limit 10
```

截图保存到 `X内容调研/screenshots/`，脚本会把截图路径写回 normalized JSON。

## 3. 状态和风险

- `research_value=high`：适合进入报告证据池，但仍需人工复核。
- `research_value=medium`：适合做趋势辅助，不建议单独引用。
- `research_value=low`：信息密度不足或互动较低，只作背景观察。
- `is_noise=true`：疑似营销、搬运或低可信内容。

不要把单条高互动 Post 当作市场事实。正式写入报告前，应至少用多条 X 内容、平台数据或官方资料交叉验证。
