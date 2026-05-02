from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus, urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "screenshots"
DATA_DIR = ROOT / "data"


COUNT_PATTERNS = [
    re.compile(r"([0-9][0-9,]*(?:\+)?)[ ]+jobs found\b", re.I),
    re.compile(r"([0-9][0-9,]*(?:\+)?)[ ]+results total\b", re.I),
    re.compile(r"([0-9][0-9,]*(?:\+)?)[ ]+results\b", re.I),
    re.compile(r"(?:over|more than)[ ]+([0-9][0-9,]*(?:\+)?)[ ]+(?:jobs|projects|services|gigs|results)\b", re.I),
    re.compile(r"([0-9][0-9,]*(?:\+)?)[ ]*个职位"),
    re.compile(r"职位[^\(（]{0,40}[\(（]([0-9][0-9,]*(?:\+)?)[ ]*个[\)）]"),
    re.compile(r"找到\s*([0-9][0-9,]*(?:\+)?)\s*(?:个)?(?:职位|岗位|项目|需求|服务|结果)"),
    re.compile(r"共\s*([0-9][0-9,]*(?:\+)?)\s*(?:个)?(?:职位|岗位|项目|需求|服务|结果)"),
]

BLOCK_PATTERNS = [
    "cloudflare",
    "captcha",
    "verify you are human",
    "access denied",
    "blocked",
    "unusual traffic",
    "sign in",
    "login",
    "451",
    "not available in your region",
    "enable cookies",
    "please verify",
]


@dataclass
class Target:
    platform: str
    keyword: str
    stat_type: str
    url: str
    note: str = ""


@dataclass
class Result:
    date: str
    platform: str
    keyword: str
    stat_type: str
    url: str
    status: str
    count: str
    evidence: str
    screenshot: str
    title: str
    note: str


def slug(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "", value)
    return value[:80].strip("-") or "page"


def targets() -> list[Target]:
    upwork = [
        "AI agent",
        "LLM engineer",
        "RAG developer",
        "AI automation",
        "workflow automation",
        "chatbot developer",
        "full stack developer",
        "backend developer",
        "data analyst",
        "API integration",
    ]
    linkedin = [
        "AI agent",
        "LLM engineer",
        "Generative AI engineer",
        "automation engineer",
        "full stack developer",
        "backend developer",
        "data analyst",
        "analytics engineer",
    ]
    indeed = [
        "AI agent",
        "LLM engineer",
        "RAG developer",
        "software developer",
        "full stack developer",
        "data analyst",
        "business process automation",
    ]
    wellfound_roles = {
        "AI agent": "artificial-intelligence-engineer",
        "LLM engineer": "machine-learning-engineer",
        "Founding engineer AI": "engineer",
        "full stack developer": "full-stack-developer",
        "backend engineer": "backend-engineer",
        "data analyst": "data-analyst",
    }
    proginn = ["AI 智能体", "AI Agent", "RAG", "聊天机器人", "流程自动化", "软件开发", "全栈开发", "后端开发", "数据分析", "BI"]
    zbj = ["AI 智能体", "AI 开发", "软件开发", "系统开发", "全栈开发", "数据分析", "自动化", "RAG"]
    fiverr = ["AI agent", "chatbot", "RAG", "AI automation", "custom GPT"]

    rows: list[Target] = []
    rows += [
        Target("Upwork Jobs", kw, "projects", f"https://www.upwork.com/nx/search/jobs/?{urlencode({'q': kw})}")
        for kw in upwork
    ]
    rows += [
        Target(
            "LinkedIn Jobs",
            kw,
            "jobs",
            f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(kw)}&location=Remote&f_JT=C",
            "Remote / Contract",
        )
        for kw in linkedin
    ]
    rows += [
        Target(
            "Indeed",
            kw,
            "jobs",
            f"https://www.indeed.com/jobs?{urlencode({'q': kw, 'l': 'Remote', 'sc': '0kf:attr(DSQF7)jt(contract);'})}",
            "Remote / Contract",
        )
        for kw in indeed
    ]
    rows += [
        Target("Wellfound", kw, "jobs", f"https://wellfound.com/role/{role}", "role page")
        for kw, role in wellfound_roles.items()
    ]
    rows += [
        Target("程序员客栈", kw, "projects", f"https://www.proginn.com/search?keyword={quote_plus(kw)}", "public search")
        for kw in proginn
    ]
    rows += [
        Target("猪八戒", kw, "projects / 需求数", f"https://www.zbj.com/search/f/?kw={quote_plus(kw)}", "public search")
        for kw in zbj
    ]
    rows += [
        Target("Fiverr", kw, "services proxy", f"https://www.fiverr.com/search/gigs?query={quote_plus(kw)}", "gig search")
        for kw in fiverr
    ]

    rows += [
        Target("Upwork Jobs", "AI category", "projects proxy", "https://www.upwork.com/freelance-jobs/ai/", "category proxy"),
        Target("Upwork Jobs", "Automation category", "projects proxy", "https://www.upwork.com/freelance-jobs/automation/", "category proxy"),
        Target("Fiverr", "AI Development category", "services proxy", "https://www.fiverr.com/categories/programming-tech/ai-coding", "category proxy"),
        Target("Fiverr", "AI Chatbot Development category", "services proxy", "https://www.fiverr.com/categories/programming-tech/ai-coding/ai-chatbot", "category proxy"),
        Target("Fiverr", "AI Integrations category", "services proxy", "https://www.fiverr.com/categories/programming-tech/ai-coding/ai-integrations", "category proxy"),
    ]
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_count(text: str) -> tuple[str, str]:
    clean = normalize_text(text)
    for pattern in COUNT_PATTERNS:
        match = pattern.search(clean)
        if match:
            start = max(match.start() - 80, 0)
            end = min(match.end() + 120, len(clean))
            return match.group(1), clean[start:end]
    return "", clean[:260]


def detect_status(text: str, count: str, response_status: int | None) -> str:
    low = text.lower()
    if response_status and response_status >= 400:
        return "count_found_with_http_warning" if count else f"http_{response_status}"
    if count:
        return "count_found_with_login_prompt" if any(token in low for token in BLOCK_PATTERNS) else "count_found"
    if any(token in low for token in BLOCK_PATTERNS):
        return "blocked_or_login_required"
    return "no_count_found"


def parse_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def filter_targets(rows: Iterable[Target], platforms: list[str] | None) -> list[Target]:
    selected = list(rows)
    if not platforms:
        return selected
    wanted = {item.casefold() for item in platforms}
    return [row for row in selected if row.platform.casefold() in wanted]


def filter_missing_counts(rows: Iterable[Target], source_json: Path | None) -> list[Target]:
    selected = list(rows)
    if not source_json:
        return selected
    previous = json.loads(source_json.read_text(encoding="utf-8"))
    missing = {
        (item["platform"], item["keyword"])
        for item in previous
        if not item.get("count")
    }
    return [row for row in selected if (row.platform, row.keyword) in missing]


def scrape(
    rows: Iterable[Target],
    limit: int | None = None,
    wait_ms: int = 2500,
    cdp_url: str | None = None,
) -> list[Result]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    selected = list(rows)[:limit] if limit else list(rows)
    results: list[Result] = []

    with sync_playwright() as p:
        remote_browser = bool(cdp_url)
        if cdp_url:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            context.set_default_timeout(45000)
        else:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1100},
                locale="en-US",
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                ),
            )
        for index, target in enumerate(selected, start=1):
            page = context.new_page()
            try:
                page.set_viewport_size({"width": 1440, "height": 1100})
            except Exception:
                pass
            response_status = None
            title = ""
            html = ""
            screenshot = SCREENSHOT_DIR / f"{index:02d}-{slug(target.platform)}-{slug(target.keyword)}.png"
            try:
                response = page.goto(target.url, wait_until="domcontentloaded", timeout=45000)
                response_status = response.status if response else None
                page.wait_for_timeout(wait_ms)
                title = page.title()
                page.screenshot(path=str(screenshot), full_page=True)
                html = page.content()
            except PlaywrightTimeoutError:
                title = "timeout"
                try:
                    page.screenshot(path=str(screenshot), full_page=True)
                    html = page.content()
                except Exception:
                    html = ""
            except Exception as exc:
                title = f"error: {exc.__class__.__name__}"
                html = ""
            finally:
                page.close()

            text = parse_visible_text(html) if html else title
            count, evidence = extract_count(text)
            status = detect_status(text, count, response_status)
            results.append(
                Result(
                    date=date.today().isoformat(),
                    platform=target.platform,
                    keyword=target.keyword,
                    stat_type=target.stat_type,
                    url=target.url,
                    status=status,
                    count=count,
                    evidence=evidence,
                    screenshot=str(screenshot.relative_to(ROOT)) if screenshot.exists() else "",
                    title=title,
                    note=target.note,
                )
            )
            time.sleep(0.8)
        if remote_browser:
            browser.close()
        else:
            context.close()
            browser.close()
    return results


def write_markdown(results: list[Result], output: Path) -> None:
    lines = [
        f"# 渠道 Job 岗位 / 项目数量 Scraping 统计（{date.today().isoformat()}）",
        "",
        "统计说明：本文件由 `scripts/scrape_channel_jobs.py` 基于 `渠道Job搜索清单.md` 生成；使用浏览器抓取公开页面并保存核心页面截图。若页面要求登录、触发 WAF/CAPTCHA、地区限制或未公开显示总数，则不推测数字。",
        "",
        "附件：核心页面截图统一保存于 `screenshots/`；结构化抓取结果保存于 `data/` 目录。",
        "",
        "| 平台 | 关键词 | 类型 | 状态 | 公开数 | 证据片段 | 截图 | 来源 |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for item in results:
        evidence = item.evidence.replace("|", "\\|")[:180]
        screenshot = f"[png]({item.screenshot})" if item.screenshot else ""
        lines.append(
            f"| {item.platform} | `{item.keyword}` | {item.stat_type} | {item.status} | {item.count or ''} | {evidence} | {screenshot} | {item.url} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--wait-ms", type=int, default=2500)
    parser.add_argument("--cdp-url", default=None, help="Connect to an already running Chrome, e.g. http://127.0.0.1:9222")
    parser.add_argument("--platform", action="append", help="Only scrape this platform name. Can be repeated.")
    parser.add_argument("--missing-counts-from", type=Path, default=None, help="Only scrape rows that have no count in this JSON output.")
    parser.add_argument("--json", type=Path, default=DATA_DIR / f"channel_job_scrape_{date.today().isoformat()}.json")
    parser.add_argument("--md", type=Path, default=ROOT / f"渠道Job岗位数Scraping统计-{date.today().isoformat()}.md")
    args = parser.parse_args()

    rows = filter_targets(targets(), args.platform)
    rows = filter_missing_counts(rows, args.missing_counts_from)
    results = scrape(rows, limit=args.limit, wait_ms=args.wait_ms, cdp_url=args.cdp_url)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps([asdict(row) for row in results], ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(results, args.md)
    print(f"Wrote {len(results)} rows")
    print(args.json)
    print(args.md)


if __name__ == "__main__":
    main()
