# Repository Guidelines

## Project Structure & Module Organization

This repository is a document workspace, not an application codebase. The root currently contains two primary Markdown reports:

- `2026年软件及AI-Agent外包及咨询市场分析报告.md`
- `2026年软件开发、数据分析与AI-Agent外包及咨询市场深度分析报告.md`

Keep new report files in the repository root unless a clear subfolder structure is introduced later. Use descriptive Chinese filenames that match the report topic and scope.

## Build, Test, and Development Commands

There is no build system, package manager, or automated test suite configured in this repository.

Useful local validation commands:

- `rg -n "^## |^### " .` — check heading structure and numbering.
- `rg -n "TODO|待补充|TBD" .` — find unfinished sections.
- `wc -w *.md` — compare document length across reports.

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
