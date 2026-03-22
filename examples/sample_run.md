# AgentForge Sample Run

This document shows what a complete AgentForge run looks like, from survey
to generated MVP.

---

## 1. Installation

```bash
pip install agentforge
# or from source:
git clone https://github.com/agentforge/agentforge
cd agentforge
pip install -e .
```

Set up environment:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## 2. Full Pipeline Run

```bash
agentforge run
```

### Survey Phase

```
╭─────────────────────────────────────────────────────╮
│               Welcome / 환영합니다                    │
│                                                     │
│  AgentForge — Personal Ontology Survey              │
│                                                     │
│  20개의 질문으로 당신만의 빌딩 청사진을 만듭니다.         │
│  20 questions to map your unique builder DNA.       │
│                                                     │
│  약 5–8분 소요됩니다. (Approx 5–8 minutes)            │
╰─────────────────────────────────────────────────────╯

──────────────── Q1. 주력 프로그래밍 언어 (1/20) ───────────────

  What is your primary programming language?

   1. Python
   2. TypeScript / JavaScript
   3. Go
   ...

  선택 (Enter number): 1
  선택됨: Python
```

### Personal Ontology Generated

```
╭──────────────────── Your Personal Ontology ────────────────────╮
│ Builder Style:    builder                                       │
│ Risk Profile:     moderate                                      │
│ Time Horizon:     3–6 months                                    │
│ Target Persona:   Developers building AI-powered tools          │
│ Monetization:     Open-core with premium cloud features         │
│ Geo Advantage:    Korean market with global English tooling     │
│                                                                 │
│ Strengths:                                                      │
│   + Strong Python expertise with AI/ML libraries                │
│   + Deep experience using Claude Code daily                     │
│   + Fintech domain knowledge with API integration skills        │
│                                                                 │
│ Gaps:                                                           │
│   - Limited frontend/UI experience                              │
│   - No prior product marketing experience                       │
│                                                                 │
│ Opportunities:                                                  │
│   * Claude Code plugin ecosystem is nascent                     │
│   * Korean developer community underserved by AI tools          │
│   * Financial data analysis pipelines lack LLM integration      │
╰─────────────────────────────────────────────────────────────────╯
```

### Environment Scan

```
                  Local Environment Scan Results
┌─────────────────────┬────────────────────────────────────────┐
│ Category            │ Details                                │
├─────────────────────┼────────────────────────────────────────┤
│ Python Version      │ 3.12.1                                 │
│ Python Packages     │ 247 installed                          │
│ AI SDKs             │ anthropic, openai                      │
│ Node.js             │ 20.11.0                                │
│ VS Code Extensions  │ 23 installed                           │
│ Claude Skills       │ code-review, refactor, test-writer     │
│ MCP Servers         │ filesystem, github, sequential-thinking│
│ Nearby Git Repos    │ 12 found                               │
╰─────────────────────┴────────────────────────────────────────╯
```

### GitHub Search Results (excerpt)

```
         Top 15 Trending AI/Agent Repos
┌───────────────────────────┬────────┬──────────────────┐
│ Repo                      │ Stars  │ Category         │
├───────────────────────────┼────────┼──────────────────┤
│ microsoft/autogen         │ 34,521 │ agent-frameworks │
│ langchain-ai/langchain    │ 89,234 │ llm-tools        │
│ openai/swarm              │ 18,902 │ agent-frameworks │
│ anthropics/claude-tools   │  5,421 │ developer-tools  │
╰───────────────────────────┴────────┴──────────────────╯
```

### Gap Analysis (excerpt)

```
╭─────────────────────── Ecosystem Summary ───────────────────────╮
│ The AI agent framework landscape is crowded at the orchestration │
│ layer but critically underserved at the developer experience     │
│ layer. Most frameworks assume deep ML knowledge. There is a      │
│ massive gap in tools that help non-ML developers productively    │
│ use agents in domain-specific applications.                      │
╰─────────────────────────────────────────────────────────────────╯

Top Opportunities
┌───┬──────────────────────────────────┬─────────┬─────────────┐
│ # │ Opportunity                      │Potential│ Competition │
├───┼──────────────────────────────────┼─────────┼─────────────┤
│ 1 │ Domain-Specific Agent Templates  │  9/10   │    low      │
│ 2 │ Claude Code Skill Marketplace    │  8/10   │    low      │
│ 3 │ Agent Output Evaluation Toolkit  │  8/10   │   medium    │
│ 4 │ LLM-Powered Financial Analyzer   │  7/10   │   medium    │
╰───┴──────────────────────────────────┴─────────┴─────────────╯
```

### Top-5 Recommendations

```
╭─────────────────── #1 — ClaudeSkillForge ──────────────────────╮
│ A marketplace and CLI for sharing, installing, and monetizing   │
│ Claude Code skills — the missing npm for Claude agents.         │
│                                                                 │
│ Why it fits you: Your daily Claude Code usage gives you deep    │
│ insight into skill gaps. Your Python expertise and MCP server   │
│ experience directly applies to building the infrastructure.     │
│                                                                 │
│ Market Opportunity: 9/10  Difficulty: 5/10  MVP: ~6 weeks       │
│ Tech Stack: Python, FastAPI, SQLite, httpx, Click, Rich         │
│                                                                 │
│ Differentiation: Unlike generic plugin stores, this is Claude-  │
│ specific, with skill testing, versioning, and revenue sharing.  │
│                                                                 │
│ First Steps:                                                    │
│   1. Build CLI: agentskill install <name>                       │
│   2. Create skill schema (YAML descriptor + Python runner)      │
│   3. Stand up FastAPI registry with GitHub OAuth                │
╰─────────────────────────────────────────────────────────────────╯
```

---

## 3. Individual Commands

```bash
# Just run the survey
agentforge survey

# Just scan your environment
agentforge scan

# Just search GitHub (custom params)
agentforge search --days 60 --limit 15

# Get recommendations (after survey + search)
agentforge recommend

# Build MVP for recommendation #2
agentforge build 2

# Full run, skip GitHub search, auto-build top pick
agentforge run --skip-github --auto-build
```

---

## 4. Generated MVP Structure

After selecting recommendation #1 (ClaudeSkillForge):

```
claudeskillforge_20260321_143022/
├── README.md                    Project overview and setup
├── pyproject.toml               Package configuration
├── requirements.txt             Python dependencies
├── .env.example                 Environment variable template
├── Makefile                     Common development tasks
├── claudeskillforge/
│   ├── __init__.py              Package init
│   ├── cli.py                   Click CLI entry point
│   ├── registry.py              Skill registry client
│   ├── installer.py             Skill installation logic
│   ├── schema.py                Pydantic models for skill descriptors
│   └── validator.py             Skill validation and testing
└── tests/
    ├── test_registry.py         Registry client tests
    └── test_installer.py        Installation flow tests
```

Setup and run:

```bash
cd claudeskillforge_20260321_143022
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
python -m claudeskillforge --help
```

---

## 5. Tips

- **Save your session**: All outputs (ontology, scan, recommendations) are
  saved to `./agentforge_output/` so you can resume without re-running.

- **Use a GitHub token**: Without `GITHUB_TOKEN`, the GitHub search is rate-
  limited to 60 requests/hour. Add your token to `.env` for 5000/hour.

- **Re-run just the build**: Once you have recommendations, run
  `agentforge build 3` to build a different option without redoing everything.

- **Iterate**: The generated MVP is a starting point. AgentForge gets you
  from zero to running code in minutes — then you take it from there.
