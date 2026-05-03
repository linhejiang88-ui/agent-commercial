from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCREENSHOT_DIR = ROOT / "screenshots"

DEFAULT_QUERIES = [
    {
        "name": "AI 赚钱真实复盘",
        "query": '("how I made" OR "I made") ("with AI" OR "using AI") ("revenue" OR "MRR" OR "$") -giveaway -"free credits" -airdrop -hiring -jobs',
        "topic": "AI 赚钱复盘",
    },
    {
        "name": "AI 工具产品化复盘",
        "query": '("I built" OR "I launched") ("AI tool" OR "AI app" OR "AI SaaS") ("MRR" OR "revenue" OR "users" OR "$") -giveaway -"free credits" -airdrop -hiring -jobs',
        "topic": "AI 工具产品化",
    },
    {
        "name": "AI 自动化赚钱复盘",
        "query": '("AI automation" OR "n8n" OR "Make.com") ("revenue" OR "MRR" OR "$" OR "clients") ("built" OR "case study" OR "workflow") -giveaway -"free credits" -airdrop -hiring -jobs',
        "topic": "AI 自动化赚钱",
    },
    {
        "name": "AI 内容产品变现",
        "query": '("AI newsletter" OR "AI course" OR "AI templates" OR "AI prompts") ("revenue" OR "sold" OR "MRR" OR "$") -giveaway -"free credits" -airdrop -hiring -jobs',
        "topic": "AI 内容产品",
    },
    {
        "name": "中文 AI 赚钱分享",
        "query": '("AI赚钱" OR "用AI赚钱" OR "AI副业" OR "AI工具") ("收入" OR "变现" OR "案例" OR "复盘") -抽奖 -空投',
        "topic": "中文 AI 变现",
    },
]

MONEY_TERMS = [
    "revenue",
    "pricing",
    "price",
    "paid",
    "client",
    "clients",
    "customer",
    "customers",
    "agency",
    "consulting",
    "implementation",
    "make money",
    "side hustle",
    "launched",
    "sold",
    "built",
    "case study",
    "newsletter",
    "template",
    "templates",
    "course",
    "ebook",
    "youtube",
    "faceless",
    "automation",
    "roi",
    "save time",
    "cost",
    "budget",
    "$",
    "mrr",
    "arr",
    "赚钱",
    "收入",
    "客户",
    "报价",
    "咨询",
    "外包",
    "接单",
    "副业",
    "变现",
    "复盘",
]

NOISE_TERMS = [
    "giveaway",
    "airdrop",
    "free credits",
    "repost + comment",
    "repost and comment",
    "comment \"",
    "reply \"",
    "follow +",
    "follow and",
    "sign up for your free trial",
    "we are hiring",
    "job opening",
    "apply now",
    "99% won’t disclose",
    "99% won't disclose",
    "99% won’t reveal",
    "99% won't reveal",
    "want to make $1,000",
    "want to earn $1,000",
    "in just one week",
]


@dataclass
class SearchSpec:
    name: str
    query: str
    topic: str


@dataclass
class XPost:
    scrape_date: str
    query_name: str
    query: str
    topic: str
    source_url: str
    author_handle: str
    text: str
    signal_type: str
    heat_score: int
    heat_label: str
    money_signal: str
    screenshot: str


def slug(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "", value)
    return value[:80].strip("-") or "x"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def build_search_url(query: str, mode: str) -> str:
    suffix = f"&f={mode}" if mode else ""
    return f"https://x.com/search?q={quote(query)}&src=typed_query{suffix}"


def signal_type(text: str) -> str:
    low = text.lower()
    if any(term in low for term in ["pricing", "price", "$", "budget", "cost", "mrr", "arr", "revenue", "报价", "收入"]):
        return "价格/收入"
    if any(term in low for term in ["make money", "side hustle", "副业", "变现", "赚钱"]):
        return "赚钱方法"
    if any(term in low for term in ["launched", "sold", "built", "case study", "复盘", "案例"]):
        return "案例复盘"
    if any(term in low for term in ["client", "customer", "lead", "business", "需求", "客户"]):
        return "客户需求"
    if any(term in low for term in ["agency", "consulting", "service", "implementation", "外包", "咨询", "接单"]):
        return "服务供给"
    if any(term in low for term in ["case study", "built", "launched", "shipped", "implemented", "上线", "案例"]):
        return "案例"
    if any(term in low for term in ["tool", "platform", "api", "saas", "工具", "平台"]):
        return "工具/产品"
    return "观点"


def heat_score(text: str) -> int:
    score = 0
    low = text.lower()
    if any(term in low for term in NOISE_TERMS):
        return 0
    score += sum(3 for term in MONEY_TERMS if term in low)
    if re.search(r"\$[0-9][0-9,]*(?:k|m)?", low):
        score += 8
    if re.search(r"\b(?:made|earned|sold|launched|built)\b", low):
        score += 5
    if re.search(r"\b(?:mrr|arr|revenue|profit)\b", low):
        score += 6
    if re.search(r"\b[0-9][0-9,]*(?:\+)?\s*(?:clients|customers|users|leads)\b", low):
        score += 5
    if any(term in low for term in ["case study", "how i", "made", "closed", "landed", "roi"]):
        score += 4
    return score


def heat_label(score: int) -> str:
    if score >= 14:
        return "high"
    if score >= 7:
        return "medium"
    return "low"


def money_signal(text: str) -> str:
    clean = normalize_text(text)
    patterns = [
        r"\$[0-9][0-9,]*(?:\.[0-9]+)?(?:k|m)?",
        r"[0-9][0-9,]*(?:\+)?\s*(?:clients|customers|users|leads)",
        r"(?:make money|side hustle|revenue|profit|pricing|budget|ROI|MRR|ARR|launched|sold|built|case study|副业|变现|赚钱|收入|复盘)[^.。!?]{0,100}",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean, re.I)
        if match:
            start = max(match.start() - 60, 0)
            end = min(match.end() + 100, len(clean))
            return clean[start:end]
    return clean[:160]


def is_noise(text: str) -> bool:
    low = text.lower()
    return any(term in low for term in NOISE_TERMS)


def extract_handle_and_url(article) -> tuple[str, str]:
    anchors = article.locator("a").all()
    handle = ""
    source_url = ""
    for anchor in anchors:
        href = anchor.get_attribute("href") or ""
        if re.fullmatch(r"/[^/\s]+", href) and not handle:
            handle = href.strip("/")
        if "/status/" in href and not source_url:
            source_url = "https://x.com" + href.split("?")[0] if href.startswith("/") else href.split("?")[0]
    return handle, source_url


def collect_search(page, spec: SearchSpec, scrolls: int, wait_ms: int, screenshot_dir: Path) -> list[XPost]:
    url = build_search_url(spec.query, "top")
    screenshot_path = screenshot_dir / f"{slug(spec.name)}.png"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(wait_ms)
        for _ in range(scrolls):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(wait_ms)
        page.screenshot(path=str(screenshot_path), full_page=True)
    except PlaywrightTimeoutError:
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            pass

    posts: list[XPost] = []
    for article in page.locator("article").all()[:25]:
        text = normalize_text(article.inner_text(timeout=5000))
        if len(text) < 80:
            continue
        handle, source_url = extract_handle_and_url(article)
        score = heat_score(text)
        if is_noise(text):
            continue
        posts.append(
            XPost(
                scrape_date=date.today().isoformat(),
                query_name=spec.name,
                query=spec.query,
                topic=spec.topic,
                source_url=source_url,
                author_handle=handle,
                text=text,
                signal_type=signal_type(text),
                heat_score=score,
                heat_label=heat_label(score),
                money_signal=money_signal(text),
                screenshot=str(screenshot_path.relative_to(ROOT)) if screenshot_path.exists() else "",
            )
        )
    return posts


def dedupe(posts: list[XPost]) -> list[XPost]:
    seen: set[str] = set()
    output: list[XPost] = []
    for post in sorted(posts, key=lambda item: item.heat_score, reverse=True):
        text_key = re.sub(r"@[A-Za-z0-9_]+", "", post.text.lower())
        text_key = re.sub(r"\d{4}年\d+月\d+日|[a-z]+ \d+|·", "", text_key)
        text_key = re.sub(r"\s+", " ", text_key)[:260]
        keys = {post.source_url or post.text[:180], text_key}
        if seen.intersection(keys):
            continue
        seen.update(keys)
        output.append(post)
    return output


def write_markdown(posts: list[XPost], output: Path) -> None:
    by_topic: dict[str, list[XPost]] = {}
    for post in posts:
        by_topic.setdefault(post.topic, []).append(post)

    lines = [
        f"# X 商业化内容低频采集整理（{date.today().isoformat()}）",
        "",
        "采集说明：本文件由 `scripts/scrape_x_cdp.py` 连接本机已登录 Chrome CDP 生成；仅低频访问公开搜索结果页，不做点赞、关注、转发、评论或批量翻页。",
        "",
        "## 方向与热度判断",
        "",
        "| 赚钱方向 | 热度 | 主要分享类型 | 代表证据数 |",
        "| --- | --- | --- | ---: |",
    ]
    for topic, topic_posts in by_topic.items():
        max_score = max((post.heat_score for post in topic_posts), default=0)
        label = heat_label(max_score)
        signals = "；".join(sorted({post.signal_type for post in topic_posts if post.heat_score >= 4})) or "观点为主"
        lines.append(f"| {topic} | {label} | {signals} | {len(topic_posts)} |")

    lines += [
        "",
        "## 高价值帖子证据",
        "",
        "| 主题 | 热度 | 类型 | 账号 | 商业化信号 | 链接 | 截图 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    selected = [post for post in posts if post.heat_label in {"high", "medium"}]
    if not selected:
        lines.append("|  | low |  |  | 本次低频采集未发现足够明确的商业化信号。 |  |  |")
    for post in selected[:40]:
        signal = post.money_signal.replace("|", "\\|")[:220]
        handle = f"@{post.author_handle}" if post.author_handle else ""
        screenshot = f"[png]({post.screenshot})" if post.screenshot else ""
        lines.append(
            f"| {post.topic} | {post.heat_label} / {post.heat_score} | {post.signal_type} | {handle} | {signal} | {post.source_url} | {screenshot} |"
        )

    lines += [
        "",
        "## 初步赚钱方向",
        "",
        "- AI 工具赚钱：重点看是否有人分享具体工具栈、获客路径、收入数字或可复用模板。",
        "- AI 副业：重点区分真实复盘和泛泛而谈的流量帖，优先采信带 MRR、销售额、产品链接或失败教训的内容。",
        "- AI 工具产品化：常见方向包括模板、微型 SaaS、自动化脚本、Newsletter、课程、插件和垂直工作流。",
        "- AI 自动化赚钱：如果帖子能说明业务场景、交付前后效果、报价或复购，优先级高于单纯工具推荐。",
        "- 中文 AI 变现：要警惕“标题党课程/社群导流”，只有带过程、数据和案例的内容才进入高价值证据。",
        "",
        "## 风险说明",
        "",
        "- 本结果来自少量 X 搜索页采样，只能作为市场信号，不是统计口径。",
        "- X 页面可能个性化排序，热度需要结合后续多天复采和其他渠道交叉验证。",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_queries(path: Path | None) -> list[SearchSpec]:
    if not path:
        return [SearchSpec(**item) for item in DEFAULT_QUERIES]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [SearchSpec(**item) for item in payload]


def main() -> None:
    parser = argparse.ArgumentParser(description="Low-frequency X search collection through an existing Chrome CDP session.")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--queries", type=Path)
    parser.add_argument("--limit-queries", type=int, default=None)
    parser.add_argument("--scrolls", type=int, default=2)
    parser.add_argument("--wait-ms", type=int, default=6000)
    parser.add_argument("--json", type=Path, default=DATA_DIR / f"x_cdp_commercial_posts_{date.today().isoformat()}.json")
    parser.add_argument("--md", type=Path, default=ROOT / f"X商业化内容整理-{date.today().isoformat()}.md")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    specs = load_queries(args.queries)
    if args.limit_queries:
        specs = specs[: args.limit_queries]

    all_posts: list[XPost] = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(args.cdp_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        context.set_default_timeout(45000)
        page = context.new_page()
        try:
            for index, spec in enumerate(specs, start=1):
                print(f"[{index}/{len(specs)}] {spec.name}")
                all_posts.extend(collect_search(page, spec, args.scrolls, args.wait_ms, SCREENSHOT_DIR))
                time.sleep(8)
        finally:
            page.close()
            browser.close()

    posts = dedupe(all_posts)
    args.json.write_text(json.dumps([asdict(post) for post in posts], ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(posts, args.md)
    print(f"Wrote {len(posts)} posts")
    print(args.json)
    print(args.md)


if __name__ == "__main__":
    main()
