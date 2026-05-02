# Chrome CDP 抓取使用说明

本文说明 `渠道Job调研/scripts/scrape_channel_jobs.py --cdp-url` 的工作方式和使用流程。适用于复用已经打开的真实 Chrome，处理 Cloudflare、登录态、Cookie、地区跳转等无头浏览器容易失败的页面。

## 1. 工作方式

`--cdp-url` 使用 Chrome DevTools Protocol（CDP）连接一个已经启动的 Chrome。

脚本不会新开无头浏览器，而是连接到你本机正在运行的 Chrome 调试端口，例如：

```bash
http://127.0.0.1:9222
```

连接成功后，脚本会复用该 Chrome 的：

- 登录状态；
- Cookies；
- 已通过的人机验证状态；
- 浏览器指纹；
- 真实 Chrome 网络环境；
- 当前用户 Profile 的站点偏好设置。

这比无头浏览器更接近人工访问，因此 Upwork、LinkedIn、Wellfound、Fiverr 这类网站的成功率通常更高。

但它不能保证绕过所有限制。如果站点对当前 IP、账号、地区或请求频率做了硬拦截，CDP 也可能仍然返回 `403`、Cloudflare challenge 或登录页。

## 2. 启动 Chrome

必须用 `--remote-debugging-port` 启动 Chrome。普通已经打开的 Chrome 不能被脚本接管。

推荐在仓库根目录执行：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$PWD/.chrome-job-scrape" \
  --no-first-run
```

参数说明：

- `--remote-debugging-port=9222`：开放 CDP 调试端口。
- `--user-data-dir="$PWD/.chrome-job-scrape"`：使用独立 Chrome Profile，避免污染日常浏览器账号和插件环境。
- `--no-first-run`：减少首次启动提示。

如果 Chrome 已经开着但不是用这个命令启动的，建议关闭该测试 Profile 的 Chrome，再用上面的命令重新启动。

## 3. 确认 CDP 端口可用

运行：

```bash
curl -sS http://127.0.0.1:9222/json/version
```

如果成功，会看到类似：

```json
{
  "Browser": "Chrome/147.0.7727.138",
  "Protocol-Version": "1.3",
  "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/..."
}
```

如果提示连接失败，说明 Chrome 没有用 `--remote-debugging-port=9222` 启动，或端口不是 `9222`。

## 4. 先人工准备站点状态

在刚启动的 Chrome 里，建议先手动打开重点平台：

- `https://www.upwork.com/nx/search/jobs/`
- `https://www.linkedin.com/jobs/`
- `https://www.indeed.com/jobs`
- `https://wellfound.com/jobs`
- `https://www.fiverr.com/`

如果页面要求登录、验证、点选 Cloudflare、人机校验或同意 Cookie，请先手动完成。

完成后不要关闭 Chrome。脚本会连接这个正在运行的浏览器继续访问页面。

## 5. 全量抓取

从仓库根目录进入渠道 Job 调研目录后运行：

```bash
cd 渠道Job调研
../.venv-scrapling/bin/python scripts/scrape_channel_jobs.py \
  --cdp-url http://127.0.0.1:9222 \
  --wait-ms 5000
```

默认输出：

- `data/channel_job_scrape_YYYY-MM-DD.json`
- `渠道Job岗位数Scraping统计-YYYY-MM-DD.md`
- `screenshots/*.png`

`--wait-ms 5000` 表示每个页面加载后额外等待 5 秒，给动态内容、验证跳转和结果数渲染留时间。

## 6. 只补抓某个平台

如果只想补抓 Upwork：

```bash
../.venv-scrapling/bin/python scripts/scrape_channel_jobs.py \
  --cdp-url http://127.0.0.1:9222 \
  --platform "Upwork Jobs" \
  --wait-ms 5000
```

可重复传入多个平台：

```bash
../.venv-scrapling/bin/python scripts/scrape_channel_jobs.py \
  --cdp-url http://127.0.0.1:9222 \
  --platform "Upwork Jobs" \
  --platform "Fiverr" \
  --platform "Wellfound" \
  --wait-ms 5000
```

当前脚本中的平台名称包括：

- `Upwork Jobs`
- `LinkedIn Jobs`
- `Indeed`
- `Wellfound`
- `程序员客栈`
- `猪八戒`
- `Fiverr`

## 7. 只测试前几条

调试时不要直接跑全量，可以先限制条数：

```bash
../.venv-scrapling/bin/python scripts/scrape_channel_jobs.py \
  --cdp-url http://127.0.0.1:9222 \
  --platform "Upwork Jobs" \
  --limit 2 \
  --wait-ms 5000 \
  --json data/channel_job_scrape_cdp_test.json \
  --md 渠道Job岗位数Scraping统计-CDP测试.md
```

确认截图和结果正常后，再去掉 `--limit` 跑完整平台。

## 8. 单独保存 CDP 结果

为了不覆盖主报告，可以指定输出文件：

```bash
../.venv-scrapling/bin/python scripts/scrape_channel_jobs.py \
  --cdp-url http://127.0.0.1:9222 \
  --wait-ms 5000 \
  --json data/channel_job_scrape_cdp_2026-05-02.json \
  --md 渠道Job岗位数Scraping统计-CDP-2026-05-02.md
```

确认 CDP 结果更好后，再手动同步为主结果。

## 9. 状态字段含义

报告中的 `状态` 字段用于区分结果可信度：

- `count_found`：公开页面中提取到结果数。
- `count_found_with_login_prompt`：提取到结果数，但页面同时出现登录提示。
- `count_found_with_http_warning`：HTTP 状态异常或有警告，但页面文本中仍能提取到结果数，需要人工复核截图。
- `http_403`：页面被 WAF、Cloudflare 或权限策略拦截。
- `http_429`：请求频率过高。
- `blocked_or_login_required`：页面要求登录、人机验证或地区不可用。
- `no_count_found`：页面可访问，但没有发现稳定的公开总数。

## 10. 常见问题

### 端口连不上

现象：

```bash
curl: (7) Failed to connect to 127.0.0.1 port 9222
```

处理：

- 确认 Chrome 是用 `--remote-debugging-port=9222` 启动的；
- 确认没有把端口改成其他数字；
- 关闭测试 Chrome 后重新执行启动命令。

### CDP 成功但仍然 Cloudflare 403

说明当前 Chrome Profile 没有真正通过该站点验证，或站点对 IP / 账号 / 地区做了硬拦截。

处理：

- 在该 Chrome 中手动打开对应 URL；
- 完成登录或验证；
- 保持 Chrome 不关闭；
- 重新跑对应平台。

### 脚本打开页面很慢

CDP 模式使用真实 Chrome，会加载更多资源，通常比无头模式慢。

处理：

- 用 `--platform` 缩小范围；
- 用 `--limit` 先测试；
- 只对被 WAF 拦截的平台使用 CDP。

### LinkedIn 数字需要复核

LinkedIn 页面有时会同时显示标题总数、筛选项数量、列表序号。脚本已尽量只提取总量表达，但仍建议结合截图人工复核高价值关键词。

## 11. 推荐流程

1. 用 CDP 命令启动独立 Chrome Profile。
2. 手动访问重点平台并完成登录 / 验证。
3. 用 `curl` 确认 `http://127.0.0.1:9222/json/version` 可访问。
4. 先用 `--platform` 和 `--limit` 小范围测试。
5. 再全量或按平台补抓。
6. 打开 Markdown 报告和截图，人工复核 `count_found_with_login_prompt`、`count_found_with_http_warning` 和高价值关键词。
