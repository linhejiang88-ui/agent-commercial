# GitHub 机会调研使用说明

本文说明如何用 `scripts/analyze_github_opportunities.py` 从 GitHub Search API 中找 AI / AI 工具商业化机会。

## 1. 配置

脚本可以不配置 token 低频运行，但建议配置 `GITHUB_TOKEN` 提高额度：

```bash
export GITHUB_TOKEN="你的 GitHub token"
```

Token 只需要公开仓库读取权限，不需要写权限。

## 2. 小样本运行

从仓库根目录执行：

```bash
python3 GitHub机会调研/scripts/analyze_github_opportunities.py \
  --limit 5 \
  --json GitHub机会调研/data/github_opportunities_YYYY-MM-DD.json \
  --md GitHub机会调研/GitHub商业化机会分析-YYYY-MM-DD.md
```

默认读取脚本内置搜索词，并输出：

- `GitHub机会调研/data/github_opportunities_YYYY-MM-DD.json`
- `GitHub机会调研/GitHub商业化机会分析-YYYY-MM-DD.md`

## 3. 自定义搜索

可以传入查询 JSON：

```bash
python3 GitHub机会调研/scripts/analyze_github_opportunities.py \
  --queries GitHub机会调研/data/github_queries.json \
  --limit 10
```

查询文件格式：

```json
[
  {
    "name": "AI Agent",
    "query": "AI agent stars:>500 pushed:>2026-01-01",
    "topic": "AI Agent"
  }
]
```

## 4. 输出字段

每个 repo 会记录：

- `full_name`
- `html_url`
- `description`
- `stars`
- `forks`
- `open_issues`
- `pushed_at`
- `created_at`
- `language`
- `topics`
- `license`
- `score_total`
- `opportunity_type`
- `commercialization_paths`
- `risk_notes`

## 5. 评分口径

脚本先做自动粗筛，最终仍需人工复核 issue 和 README。

自动评分重点：

- stars 和 forks：判断采用度。
- open issues：判断痛点和支持需求。
- 最近更新时间：判断项目是否活跃。
- topics / description：判断是否匹配 AI 自动化、RAG、Agent、插件、工作流。
- license：判断二次封装风险。

不要只按分数决策。高分 repo 可能竞争很重，低分 repo 也可能代表垂直早期机会。
