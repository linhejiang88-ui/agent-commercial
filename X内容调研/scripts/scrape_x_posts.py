from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCREENSHOT_DIR = ROOT / "screenshots"
UTC = timezone.utc

RECENT_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
RECENT_COUNTS_URL = "https://api.x.com/2/tweets/counts/recent"

DEFAULT_QUERIES = [
    {
        "name": "AI Agent 外包/咨询",
        "query": '"AI agent" ("freelancer" OR "agency" OR "consulting" OR "automation") lang:en -is:retweet',
        "topic": "AI Agent",
    },
    {
        "name": "Workflow Automation 客户需求",
        "query": '"workflow automation" ("client" OR "business" OR "agency") lang:en -is:retweet',
        "topic": "自动化",
    },
    {
        "name": "RAG 企业实施",
        "query": '"RAG" ("consulting" OR "implementation" OR "enterprise") lang:en -is:retweet',
        "topic": "RAG",
    },
    {
        "name": "AI Automation 接单平台",
        "query": '"AI automation" ("Upwork" OR "Fiverr" OR "client") lang:en -is:retweet',
        "topic": "外包渠道",
    },
    {
        "name": "中文 AI 智能体外包",
        "query": '("AI智能体" OR "智能体") ("外包" OR "接单" OR "咨询") lang:zh -is:retweet',
        "topic": "中文市场",
    },
]

TWEET_FIELDS = [
    "author_id",
    "conversation_id",
    "created_at",
    "entities",
    "lang",
    "public_metrics",
    "referenced_tweets",
]
USER_FIELDS = ["description", "name", "public_metrics", "username"]


@dataclass
class QuerySpec:
    name: str
    query: str
    topic: str


@dataclass
class NormalizedPost:
    scrape_date: str
    query_name: str
    query: str
    topic: str
    signal_type: str
    research_value: str
    evidence_note: str
    is_noise: bool
    id: str
    text: str
    created_at: str
    author_id: str
    author_username: str
    author_name: str
    author_description: str
    lang: str
    public_metrics: dict[str, Any]
    author_metrics: dict[str, Any]
    conversation_id: str
    source_url: str


def parse_time(value: str | None, default: datetime) -> str:
    if not value:
        dt = default
    else:
        raw = value.strip()
        if len(raw) == 10:
            dt = datetime.fromisoformat(raw).replace(tzinfo=UTC)
        else:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_queries(path: Path | None) -> list[QuerySpec]:
    if not path:
        return [QuerySpec(**item) for item in DEFAULT_QUERIES]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [QuerySpec(**item) for item in payload]


def request_json(url: str, token: str, params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    target = f"{url}?{urlencode(params, doseq=True)}"
    request = Request(target, headers={"Authorization": f"Bearer {token}"})
    while True:
        try:
            with urlopen(request, timeout=60) as response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                return json.loads(response.read().decode("utf-8")), headers
        except HTTPError as exc:
            headers = {key.lower(): value for key, value in exc.headers.items()}
            if exc.code == 429 and headers.get("x-rate-limit-reset"):
                reset_at = int(headers["x-rate-limit-reset"])
                wait_seconds = max(reset_at - int(time.time()) + 2, 5)
                print(f"Rate limited. Waiting {wait_seconds}s until reset.")
                time.sleep(wait_seconds)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"X API request failed: HTTP {exc.code} {body}") from exc


def count_query(token: str, query: QuerySpec, start_time: str, end_time: str) -> int:
    payload, _headers = request_json(
        RECENT_COUNTS_URL,
        token,
        {
            "query": query.query,
            "start_time": start_time,
            "end_time": end_time,
            "granularity": "day",
        },
    )
    return int(payload.get("meta", {}).get("total_tweet_count", 0))


def search_query(
    token: str,
    query: QuerySpec,
    start_time: str,
    end_time: str,
    max_pages: int,
    raw_file: Path,
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    next_token = ""
    for page_index in range(max_pages):
        params: dict[str, Any] = {
            "query": query.query,
            "start_time": start_time,
            "end_time": end_time,
            "max_results": 100,
            "tweet.fields": ",".join(TWEET_FIELDS),
            "expansions": "author_id",
            "user.fields": ",".join(USER_FIELDS),
        }
        if next_token:
            params["next_token"] = next_token
        payload, headers = request_json(RECENT_SEARCH_URL, token, params)
        record = {
            "scrape_date": date.today().isoformat(),
            "query_name": query.name,
            "query": query.query,
            "topic": query.topic,
            "page_index": page_index + 1,
            "rate_limit_remaining": headers.get("x-rate-limit-remaining", ""),
            "rate_limit_reset": headers.get("x-rate-limit-reset", ""),
            "payload": payload,
        }
        with raw_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        pages.append(record)
        next_token = payload.get("meta", {}).get("next_token", "")
        if not next_token:
            break
    return pages


def classify_signal(text: str) -> str:
    low = text.lower()
    if any(term in low for term in ["hiring", "job", "role", "recruit", "looking for"]):
        return "招聘"
    if any(term in low for term in ["client", "customer", "need", "looking to", "request"]):
        return "需求"
    if any(term in low for term in ["price", "pricing", "$", "budget", "cost", "quote"]):
        return "价格"
    if any(term in low for term in ["case study", "shipped", "built", "launched", "implemented"]):
        return "案例"
    if any(term in low for term in ["tool", "platform", "product", "sdk", "api"]):
        return "工具"
    if any(term in low for term in ["pain", "problem", "hard", "broken", "struggle"]):
        return "痛点"
    return "观点"


def score_research_value(text: str, metrics: dict[str, Any], author_metrics: dict[str, Any]) -> tuple[str, str, bool]:
    low = text.lower()
    engagement = sum(int(metrics.get(key, 0) or 0) for key in ["like_count", "retweet_count", "reply_count", "quote_count"])
    followers = int(author_metrics.get("followers_count", 0) or 0)
    concrete_terms = ["client", "customer", "budget", "pricing", "case study", "hiring", "launched", "implemented", "外包", "接单", "客户", "报价"]
    is_concrete = any(term in low for term in concrete_terms)
    is_noise = any(term in low for term in ["giveaway", "airdrop", "follow me", "dm me for promo"])
    if is_noise:
        return "low", "疑似营销或低信息密度内容。", True
    if is_concrete and (engagement >= 20 or followers >= 5000):
        return "high", "包含具体市场信号，且互动或账号影响力较高。", False
    if is_concrete or engagement >= 10:
        return "medium", "包含可归纳信号，可作为辅助证据。", False
    return "low", "信息密度或互动较低，暂作背景观察。", False


def normalize_pages(pages: list[dict[str, Any]]) -> list[NormalizedPost]:
    posts: list[NormalizedPost] = []
    seen: set[str] = set()
    for page in pages:
        payload = page["payload"]
        users = {item["id"]: item for item in payload.get("includes", {}).get("users", [])}
        for item in payload.get("data", []) or []:
            tweet_id = item["id"]
            if tweet_id in seen:
                continue
            seen.add(tweet_id)
            user = users.get(item.get("author_id", ""), {})
            username = user.get("username", "")
            source_url = f"https://x.com/{username}/status/{tweet_id}" if username else f"https://x.com/i/web/status/{tweet_id}"
            metrics = item.get("public_metrics", {}) or {}
            author_metrics = user.get("public_metrics", {}) or {}
            value, note, is_noise = score_research_value(item.get("text", ""), metrics, author_metrics)
            posts.append(
                NormalizedPost(
                    scrape_date=page["scrape_date"],
                    query_name=page["query_name"],
                    query=page["query"],
                    topic=page["topic"],
                    signal_type=classify_signal(item.get("text", "")),
                    research_value=value,
                    evidence_note=note,
                    is_noise=is_noise,
                    id=tweet_id,
                    text=item.get("text", ""),
                    created_at=item.get("created_at", ""),
                    author_id=item.get("author_id", ""),
                    author_username=username,
                    author_name=user.get("name", ""),
                    author_description=user.get("description", ""),
                    lang=item.get("lang", ""),
                    public_metrics=metrics,
                    author_metrics=author_metrics,
                    conversation_id=item.get("conversation_id", ""),
                    source_url=source_url,
                )
            )
    posts.sort(key=lambda post: (post.research_value != "high", post.created_at), reverse=False)
    return posts


def write_markdown(posts: list[NormalizedPost], counts: dict[str, int], output: Path) -> None:
    lines = [
        f"# X 市场信号整理（{date.today().isoformat()}）",
        "",
        "统计说明：本文件由 `scripts/scrape_x_posts.py` 基于 X API Recent Search 生成；仅整理公开 Posts，不抓取私信、受保护账号或登录后不可公开验证的内容。",
        "",
        "## 查询概览",
        "",
        "| 查询 | 近 7 天计数 |",
        "| --- | ---: |",
    ]
    for name, count in counts.items():
        lines.append(f"| {name} | {count} |")
    lines += [
        "",
        "## 高价值信号",
        "",
        "| 主题 | 类型 | 账号 | 发布时间 | 互动 | 证据说明 | 链接 | 摘要 |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    selected = [post for post in posts if post.research_value == "high" and not post.is_noise]
    if not selected:
        lines.append("|  |  |  |  |  | 暂无高价值信号，建议扩大关键词或时间窗口。 |  |  |")
    for post in selected[:50]:
        metrics = post.public_metrics
        engagement = sum(int(metrics.get(key, 0) or 0) for key in ["like_count", "retweet_count", "reply_count", "quote_count"])
        text = post.text.replace("\n", " ").replace("|", "\\|")[:180]
        lines.append(
            f"| {post.topic} | {post.signal_type} | @{post.author_username} | {post.created_at} | {engagement} | {post.evidence_note} | {post.source_url} | {text} |"
        )
    lines += [
        "",
        "## 后续处理建议",
        "",
        "- 对高价值信号打开原始链接复核，并用 `screenshot` 子命令保存截图。",
        "- 报告正文只引用归纳后的市场信号，不直接堆叠原文。",
        "- 对营销号、搬运号、无法验证的夸张数据保持 `low` 或 `is_noise=true`。",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_search(args: argparse.Namespace) -> None:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing X_BEARER_TOKEN. Export your X API bearer token before running.")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    start_time = parse_time(args.start_time, datetime.now(UTC) - timedelta(days=7))
    end_time = parse_time(args.end_time, datetime.now(UTC) - timedelta(minutes=1))
    queries = load_queries(args.queries)
    if args.query:
        queries = [QuerySpec(name=f"custom-{index}", query=value, topic="自定义") for index, value in enumerate(args.query, start=1)]

    raw_file = args.raw_jsonl or DATA_DIR / f"x_posts_raw_{date.today().isoformat()}.jsonl"
    normalized_file = args.normalized_json or DATA_DIR / f"x_posts_normalized_{date.today().isoformat()}.json"
    markdown_file = args.md or ROOT / f"X市场信号整理-{date.today().isoformat()}.md"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text("", encoding="utf-8")

    pages: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for query in queries:
        print(f"Counting: {query.name}")
        counts[query.name] = count_query(token, query, start_time, end_time)
        print(f"Searching: {query.name}")
        pages.extend(search_query(token, query, start_time, end_time, args.max_pages, raw_file))

    posts = normalize_pages(pages)
    normalized_file.parent.mkdir(parents=True, exist_ok=True)
    normalized_file.write_text(json.dumps([asdict(post) for post in posts], ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(posts, counts, markdown_file)
    print(f"Wrote raw responses: {raw_file}")
    print(f"Wrote normalized posts: {normalized_file}")
    print(f"Wrote markdown report: {markdown_file}")


def run_screenshot(args: argparse.Namespace) -> None:
    from playwright.sync_api import sync_playwright

    posts = json.loads(args.input.read_text(encoding="utf-8"))
    selected = [post for post in posts if post.get("research_value") == args.value and not post.get("is_noise")]
    selected = selected[: args.limit]
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        if args.cdp_url:
            browser = p.chromium.connect_over_cdp(args.cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
        else:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1100}, locale="en-US")
        context.set_default_timeout(args.timeout_ms)
        for index, post in enumerate(selected, start=1):
            username = post.get("author_username") or "x"
            tweet_id = post["id"]
            path = SCREENSHOT_DIR / f"{index:02d}-{username}-{tweet_id}.png"
            page = context.new_page()
            try:
                page.goto(post["source_url"], wait_until="domcontentloaded", timeout=args.timeout_ms)
                page.wait_for_timeout(args.wait_ms)
                page.screenshot(path=str(path), full_page=True)
                post["screenshot"] = str(path.relative_to(ROOT))
                print(f"Saved {path}")
            finally:
                page.close()
        args.input.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.cdp_url:
            browser.close()
        else:
            context.close()
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect public X posts for market research.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Fetch public posts through X API Recent Search.")
    search.add_argument("--queries", type=Path, help="JSON file containing name/query/topic objects.")
    search.add_argument("--query", action="append", help="Override defaults with one or more custom X search queries.")
    search.add_argument("--start-time", help="UTC ISO time or YYYY-MM-DD. Defaults to 7 days ago.")
    search.add_argument("--end-time", help="UTC ISO time or YYYY-MM-DD. Defaults to now minus one minute.")
    search.add_argument("--max-pages", type=int, default=1, help="Pages per query. Each page can return up to 100 posts.")
    search.add_argument("--raw-jsonl", type=Path)
    search.add_argument("--normalized-json", type=Path)
    search.add_argument("--md", type=Path)
    search.set_defaults(func=run_search)

    screenshot = subparsers.add_parser("screenshot", help="Save browser screenshots for selected normalized posts.")
    screenshot.add_argument("--input", type=Path, required=True, help="Normalized JSON file to update with screenshot paths.")
    screenshot.add_argument("--value", default="high", choices=["high", "medium", "low"])
    screenshot.add_argument("--limit", type=int, default=10)
    screenshot.add_argument("--cdp-url", help="Connect to an existing Chrome, e.g. http://127.0.0.1:9222")
    screenshot.add_argument("--wait-ms", type=int, default=5000)
    screenshot.add_argument("--timeout-ms", type=int, default=45000)
    screenshot.set_defaults(func=run_screenshot)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
