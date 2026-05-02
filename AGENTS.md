# Repository Guidelines

## Project Structure & Module Organization

This repository is a document workspace, not an application codebase. The root contains the primary market reports and navigation documents:

- `2026年软件及AI-Agent外包及咨询市场分析报告.md`
- `2026年软件及AI-Agent外包及咨询市场分析报告（插图版）.md`
- `2026年软件开发、数据分析与AI-Agent外包及咨询市场深度分析报告.md`
- `2025-2026四大接单平台数据分析报告.md`
- `README.md`
- `报告插图规划.md`

Channel job scraping materials are grouped under `渠道Job调研/`:

- `渠道Job调研/*.md` — channel job search lists, scraping reports, and CDP usage notes.
- `渠道Job调研/data/` — structured JSON scraping outputs.
- `渠道Job调研/screenshots/` — core page screenshots linked from scraping reports.
- `渠道Job调研/scripts/` — scraping scripts for this dataset.

Keep new top-level market reports in the repository root. Put channel job related files in `渠道Job调研/`, and use descriptive Chinese filenames that match the report topic and scope.

## Build, Test, and Development Commands

There is no build system, package manager, or automated test suite configured in this repository.

Useful local validation commands:

- `rg -n "^## |^### " .` — check heading structure and numbering.
- `rg -n "TODO|待补充|TBD" .` — find unfinished sections.
- `wc -w *.md` — compare document length across reports.
- `rg -n "images/channel-job-screenshots|screenshots/channel_jobs" .` — ensure channel job links do not point to old screenshot locations.
- `for f in images/*.svg; do xmllint --noout "$f" || exit 1; done` — validate generated SVG report figures.

If you add tooling later, document the exact commands here.

## Coding Style & Naming Conventions

Write in Markdown with clear heading hierarchy and short paragraphs. Prefer:

- ATX headings: `#`, `##`, `###`
- Flat bullet lists over deeply nested lists
- Consistent terminology for `ITO`, `BPO`, `KPO`, and `AI Agent`

Use full-width Chinese punctuation in Chinese prose, and keep English acronyms exactly as published in source material. When revising numbered sections, update all downstream headings and internal references in the same edit.

## Testing Guidelines

Validation is editorial rather than programmatic. Before finalizing changes:

- confirm heading numbers are sequential;
- verify cited figures, dates, and links against source material;
- search for stale section names after restructures.
- verify local Markdown links after moving channel job files;
- confirm JSON screenshot paths under `渠道Job调研/data/` resolve against `渠道Job调研/screenshots/`.

When adding references, prefer official or primary sources and include exact publication dates where relevant.

## Commit & Pull Request Guidelines

No Git history is available in this directory, so follow a simple imperative style for change summaries, for example:

- `docs: remove team-size analysis section`
- `docs: expand AI Coding impact on ITO/BPO/KPO`

For handoff or review, include:

- a short summary of what changed;
- affected files;
- whether section numbering, citations, or conclusions were updated.

## Source & Editing Notes

Do not introduce unsupported market figures or anecdotal percentages without a citable source. Prefer updating both reports consistently when the same structural section appears in each file.

For channel job scraping updates, prefer the CDP report as the main record:

- `渠道Job调研/渠道Job岗位数Scraping统计-CDP-2026-05-02.md`
- `渠道Job调研/data/channel_job_scrape_cdp_2026-05-02.json`
- `渠道Job调研/screenshots/`

Process reports and retry outputs can remain as evidence, but README and main report attachments should point to the CDP report unless a newer final report supersedes it.
