---
name: agentforge
description: AI 에이전트 시대에 무엇을 만들지 추천하고 MVP를 생성하는 프레임워크. Personal ontology survey → GitHub gap analysis → personalized recommendations → MVP generation. No API key needed — uses Claude Code natively.
---

# AgentForge Skill

You are running AgentForge — a framework that helps developers in the AI agent era overcome decision paralysis about what to build.

## Pipeline Steps

When the user runs /agentforge or asks to run AgentForge:

1. **Personal Ontology** — If `agentforge_output/ontology.json` exists, load it. Otherwise guide the user through 20 key questions about their skills, domain expertise, tools, pain points, time availability, target users, monetization preference, and risk tolerance. Save results to `agentforge_output/ontology.json`.

2. **Environment Scan** — Run: `python -m agentforge.scanner.tools` or scan manually:
   - Check installed Python packages: `pip list`
   - Check Claude Code skills in ~/.claude/
   - Check MCP servers in .mcp.json
   - Save to `agentforge_output/tool_profile.json`

3. **GitHub Gap Analysis** — Search GitHub for trending repos in AI/agents/knowledge-graph categories. Identify what's missing, what's incomplete, what Korean market needs. Save to `agentforge_output/gap_analysis.json`.

4. **Recommendations** — Generate top 5 personalized project recommendations based on ontology + tools + gaps. Display ranked list with fit score, market score, difficulty, MVP timeline. Save to `agentforge_output/recommendations.json`.

5. **MVP Generation** — When user selects a recommendation number, generate complete MVP code structure in `agentforge_output/mvp_[project_name]/`.

## Commands
- `agentforge run` — full pipeline
- `agentforge survey` — just do the survey
- `agentforge scan` — just scan environment
- `agentforge recommend` — get recommendations (requires ontology)
- `agentforge build <id>` — build MVP for recommendation #id
