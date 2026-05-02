# 渠道 Job 岗位 / 项目数量 Scraping 统计（2026-05-02）

统计说明：本文件由 `scripts/scrape_channel_jobs.py` 基于 `渠道Job搜索清单.md` 生成；使用浏览器抓取公开页面并保存核心页面截图。若页面要求登录、触发 WAF/CAPTCHA、地区限制或未公开显示总数，则不推测数字。

| 平台 | 关键词 | 类型 | 状态 | 公开数 | 证据片段 | 截图 | 来源 |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| Fiverr | `custom GPT` | services proxy | count_found_with_login_prompt | 694 | rvice options Seller details Budget Delivery time Pro services Instant response 694 results Sort by: Relevance F Fahad S Level 2 I will build and integrate custom gpt in your websi | [png](screenshots/channel_jobs/01-fiverr-custom-gpt.png) | https://www.fiverr.com/search/gigs?query=custom+GPT |
| Upwork Jobs | `AI category` | projects proxy | http_403 |  | AI Freelance Jobs: Work Remote & Earn Online ___ Skip to content Upwork home Sign up Back to main navigation Close main navigation Hire freelancers Admin & support AI & emerging te | [png](screenshots/channel_jobs/02-upwork-jobs-ai-category.png) | https://www.upwork.com/freelance-jobs/ai/ |
| Upwork Jobs | `Automation category` | projects proxy | no_count_found |  | Sign up for Upwork \| Client & Freelancer Accounts Upwork home Join as a client or freelancer Account type selection I'm a client, hiring for a project I'm a freelancer, looking fo | [png](screenshots/channel_jobs/03-upwork-jobs-automation-category.png) | https://www.upwork.com/freelance-jobs/automation/ |
| Fiverr | `AI Development category` | services proxy | count_found_with_login_prompt | 16,000+ | rvice options Seller details Budget Delivery time Pro services Instant response 16,000+ results Sort by: Best selling S Saeed Ahmad Level 2 I will create chatgpt, ai chatbot, opena | [png](screenshots/channel_jobs/04-fiverr-ai-development-category.png) | https://www.fiverr.com/categories/programming-tech/ai-coding |
