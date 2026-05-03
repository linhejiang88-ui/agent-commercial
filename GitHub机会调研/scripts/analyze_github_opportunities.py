from __future__ import annotations

import argparse
import http.client
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEARCH_URL = "https://api.github.com/search/repositories"


DEFAULT_QUERIES = [
    {"name": "AI Agent", "query": "\"AI agent\" stars:>500 pushed:>2026-01-01", "topic": "AI Agent"},
    {"name": "n8n AI workflow", "query": "\"n8n\" \"AI\" \"workflow\" stars:>50 pushed:>2026-01-01", "topic": "AI 自动化"},
    {"name": "RAG chatbot", "query": "\"RAG\" \"chatbot\" stars:>300 pushed:>2026-01-01", "topic": "RAG / 文档自动化"},
    {"name": "AI automation", "query": "\"AI automation\" stars:>100 pushed:>2026-01-01", "topic": "AI 自动化"},
    {"name": "Chrome AI extension", "query": "\"Chrome extension\" \"AI\" stars:>100 pushed:>2026-01-01", "topic": "AI 插件"},
    {"name": "Shopify AI", "query": "\"Shopify\" \"AI\" stars:>50 pushed:>2026-01-01", "topic": "电商 AI"},
    {"name": "Slack AI bot", "query": "\"Slack bot\" \"AI\" stars:>100 pushed:>2026-01-01", "topic": "团队协作 AI"},
    {"name": "programmatic SEO AI", "query": "\"programmatic SEO\" \"AI\" stars:>20 pushed:>2026-01-01", "topic": "AI SEO"},
    {"name": "document extraction AI", "query": "\"document extraction\" \"AI\" stars:>100 pushed:>2026-01-01", "topic": "文档自动化"},
    {"name": "meeting notes AI", "query": "\"meeting notes\" \"AI\" stars:>100 pushed:>2026-01-01", "topic": "会议 / CRM 自动化"},
]


@dataclass
class QuerySpec:
    name: str
    query: str
    topic: str


@dataclass
class RepoOpportunity:
    scrape_date: str
    query_name: str
    query: str
    topic: str
    full_name: str
    html_url: str
    description: str
    stars: int
    forks: int
    open_issues: int
    pushed_at: str
    created_at: str
    language: str
    topics: list[str]
    license: str
    score_total: int
    opportunity_type: str
    commercialization_paths: list[str]
    risk_notes: list[str]


def load_queries(path: Path | None) -> list[QuerySpec]:
    if not path:
        return [QuerySpec(**item) for item in DEFAULT_QUERIES]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [QuerySpec(**item) for item in payload]


def request_json(url: str, params: dict[str, Any], token: str) -> dict[str, Any]:
    target = f"{url}?{urlencode(params)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "software-ecosystem-market-research",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(target, headers=headers)
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {403, 429, 500, 502, 503, 504} and attempt < 3:
                time.sleep(attempt * 5)
                continue
            raise RuntimeError(f"GitHub API failed: HTTP {exc.code} {body}") from exc
        except (URLError, http.client.RemoteDisconnected) as exc:
            if attempt < 3:
                time.sleep(attempt * 5)
                continue
            raise RuntimeError(f"GitHub API request failed after retries: {exc}") from exc
    raise RuntimeError("GitHub API request failed unexpectedly")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def score_repo(item: dict[str, Any], topic: str) -> tuple[int, str, list[str], list[str]]:
    stars = int(item.get("stargazers_count") or 0)
    forks = int(item.get("forks_count") or 0)
    issues = int(item.get("open_issues_count") or 0)
    pushed_at = parse_time(item.get("pushed_at"))
    age_days = max((datetime.now(timezone.utc) - parse_time(item.get("created_at"))).days, 1)
    desc = (item.get("description") or "").lower()
    topics = [value.lower() for value in item.get("topics", [])]
    text = " ".join([desc, " ".join(topics), topic.lower()])

    score = 0
    score += min(stars // 250, 10)
    score += min(forks // 100, 5)
    score += min(issues // 20, 5)
    if (datetime.now(timezone.utc) - pushed_at).days <= 30:
        score += 5
    elif (datetime.now(timezone.utc) - pushed_at).days <= 120:
        score += 3
    if stars / age_days >= 3:
        score += 5
    elif stars / age_days >= 1:
        score += 3
    if any(term in text for term in ["workflow", "automation", "n8n", "agent", "rag", "document", "shopify", "slack", "chrome"]):
        score += 4

    paths: list[str] = []
    if any(term in text for term in ["workflow", "automation", "n8n", "make"]):
        paths += ["自动化实施包", "行业 workflow 模板", "月度维护"]
    if any(term in text for term in ["rag", "document", "pdf", "knowledge"]):
        paths += ["RAG PoC", "私有化部署", "知识库维护"]
    if any(term in text for term in ["chrome", "extension", "shopify", "slack"]):
        paths += ["插件二次封装", "垂直微 SaaS", "集成服务"]
    if any(term in text for term in ["agent", "llm", "assistant"]):
        paths += ["Agent 原型", "托管部署", "企业集成"]
    if not paths:
        paths = ["部署服务", "教程 / 模板", "集成顾问"]

    risks: list[str] = []
    license_info = item.get("license") or {}
    if not license_info:
        risks.append("未识别 license，商业复用前需人工确认。")
    if stars > 10000:
        risks.append("热度很高，可能已有成熟商业竞品。")
    if issues < 5:
        risks.append("issue 少，痛点信号可能不足。")
    if (datetime.now(timezone.utc) - pushed_at).days > 180:
        risks.append("近期维护不活跃。")

    if "automation" in text or "workflow" in text:
        opportunity_type = "AI 自动化 / Workflow"
    elif "rag" in text or "document" in text:
        opportunity_type = "RAG / 文档自动化"
    elif "chrome" in text or "shopify" in text or "slack" in text:
        opportunity_type = "插件 / 平台应用"
    elif "agent" in text:
        opportunity_type = "AI Agent"
    else:
        opportunity_type = "开发者工具 / 模板"

    return score, opportunity_type, sorted(set(paths)), risks


def is_relevant_repo(item: dict[str, Any], spec: QuerySpec) -> bool:
    full_name = (item.get("full_name") or "").lower()
    desc = (item.get("description") or "").lower()
    topics = " ".join(item.get("topics", []) or []).lower()
    text = f"{full_name} {desc} {topics}"
    negative_terms = [
        "interview",
        "leetcode",
        "algorithm",
        "dictatorship",
        "censorship",
        "political",
        "面试",
        "算法",
        "政治",
    ]
    if any(term in text for term in negative_terms):
        return False
    topic_terms = {
        "AI Agent": ["ai agent", "agent", "llm", "assistant", "mcp"],
        "AI 自动化": ["automation", "workflow", "n8n", "make", "agent", "ai"],
        "RAG / 文档自动化": ["rag", "chatbot", "document", "knowledge", "retrieval", "pdf"],
        "AI 插件": ["chrome", "extension", "browser", "plugin", "ai"],
        "电商 AI": ["shopify", "ecommerce", "commerce", "store", "ai"],
        "团队协作 AI": ["slack", "bot", "assistant", "ai"],
        "AI SEO": ["seo", "programmatic", "content", "ai"],
        "文档自动化": ["document", "extraction", "pdf", "ocr", "ai"],
        "会议 / CRM 自动化": ["meeting", "notes", "transcription", "crm", "ai"],
    }
    terms = topic_terms.get(spec.topic, ["ai"])
    return any(term in text for term in terms)


def normalize_repo(item: dict[str, Any], spec: QuerySpec) -> RepoOpportunity:
    score, opportunity_type, paths, risks = score_repo(item, spec.topic)
    license_info = item.get("license") or {}
    return RepoOpportunity(
        scrape_date=date.today().isoformat(),
        query_name=spec.name,
        query=spec.query,
        topic=spec.topic,
        full_name=item.get("full_name", ""),
        html_url=item.get("html_url", ""),
        description=item.get("description") or "",
        stars=int(item.get("stargazers_count") or 0),
        forks=int(item.get("forks_count") or 0),
        open_issues=int(item.get("open_issues_count") or 0),
        pushed_at=item.get("pushed_at", ""),
        created_at=item.get("created_at", ""),
        language=item.get("language") or "",
        topics=item.get("topics", []) or [],
        license=license_info.get("spdx_id") or license_info.get("name") or "",
        score_total=score,
        opportunity_type=opportunity_type,
        commercialization_paths=paths,
        risk_notes=risks,
    )


def search_repos(spec: QuerySpec, limit: int, token: str) -> list[RepoOpportunity]:
    payload = request_json(
        SEARCH_URL,
        {
            "q": spec.query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100),
        },
        token,
    )
    items = [item for item in payload.get("items", []) if is_relevant_repo(item, spec)]
    return [normalize_repo(item, spec) for item in items[:limit]]


def dedupe(items: list[RepoOpportunity]) -> list[RepoOpportunity]:
    seen: set[str] = set()
    output: list[RepoOpportunity] = []
    for item in sorted(items, key=lambda row: row.score_total, reverse=True):
        if item.full_name in seen:
            continue
        seen.add(item.full_name)
        output.append(item)
    return output


def write_markdown(items: list[RepoOpportunity], output: Path) -> None:
    lines = [
        f"# GitHub 商业化机会分析（{date.today().isoformat()}）",
        "",
        "统计说明：本文件由 `scripts/analyze_github_opportunities.py` 基于 GitHub Search API 生成。自动评分只做粗筛，最终机会判断必须人工复核 README、issues、license 和竞品。",
        "",
        "## 高分机会",
        "",
        "| 分数 | 类型 | Repo | Stars | Issues | 最近更新 | 商业化路径 | 风险 |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for item in items[:50]:
        paths = "；".join(item.commercialization_paths)
        risks = "；".join(item.risk_notes)
        lines.append(
            f"| {item.score_total} | {item.opportunity_type} | [{item.full_name}]({item.html_url}) | {item.stars} | {item.open_issues} | {item.pushed_at[:10]} | {paths} | {risks} |"
        )
    lines += [
        "",
        "## 复核建议",
        "",
        "- 优先打开高分 repo 的 `Issues`，搜索 `deployment`、`hosted`、`pricing`、`integration`、`rate limit`、`cost`。",
        "- 如果 issue 里反复出现部署、集成、成本、权限、托管需求，可进入服务包候选。",
        "- 如果 repo 热度高但已有成熟商业云服务，应优先考虑中文落地、行业模板或实施顾问，而不是直接做竞品。",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze GitHub repositories for commercial AI opportunities.")
    parser.add_argument("--queries", type=Path)
    parser.add_argument("--limit", type=int, default=10, help="Repositories per query.")
    parser.add_argument("--json", type=Path, default=DATA_DIR / f"github_opportunities_{date.today().isoformat()}.json")
    parser.add_argument("--md", type=Path, default=ROOT / f"GitHub商业化机会分析-{date.today().isoformat()}.md")
    parser.add_argument("--sleep", type=float, default=1.5, help="Seconds between queries.")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_items: list[RepoOpportunity] = []
    for index, spec in enumerate(load_queries(args.queries), start=1):
        print(f"[{index}] {spec.name}")
        all_items.extend(search_repos(spec, args.limit, token))
        time.sleep(args.sleep)
    items = dedupe(all_items)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(items, args.md)
    print(f"Wrote {len(items)} repos")
    print(args.json)
    print(args.md)


if __name__ == "__main__":
    main()
