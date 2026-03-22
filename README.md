# AgentForge

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No API Key](https://img.shields.io/badge/API%20Key-Not%20Required-brightgreen.svg)](#)
[![Powered by Claude Code](https://img.shields.io/badge/powered%20by-Claude%20Code-orange.svg)](https://claude.ai/download)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill%20Ready-blueviolet.svg)](#)

**What to Build in the Agent Era — AI 에이전트 시대의 선택장애 해결 프레임워크**

> **No API key needed.** AgentForge runs entirely through your locally installed Claude Code.

AgentForge helps Claude Code users and AI power-users overcome decision paralysis
about what to build next. It combines personal ontology mapping, local environment
scanning, GitHub trend analysis, and Claude-powered recommendations to produce a
personalized, immediately actionable MVP — all using your existing Claude Code session.

---

## The Problem

You use Claude Code every day. You see the potential. But when it comes to
*what to build*, you freeze.

- Too many ideas, no framework to evaluate them
- You don't know what gaps exist in the ecosystem
- You don't know which opportunities fit *your* specific skills
- Even when you pick something, starting from scratch is slow

AgentForge solves all of this in one automated pipeline.

---

## Pipeline Overview

```
                        AgentForge Pipeline
                        ===================

  [You]
    |
    v
+-------------------+
| 1. Ontology Survey|  20 questions about skills, domain,
|   (20 questions)  |  pain points, time, risk, motivation
+-------------------+
    |
    | Personal Ontology JSON
    v
+-------------------+
| 2. Env Scanner    |  pip packages, Claude skills, MCP servers,
|                   |  VS Code extensions, npm globals, git repos
+-------------------+
    |
    | ToolProfile
    v
+-------------------+
| 3. GitHub Search  |  Trending AI/agent repos across 5 categories
|                   |  (1000+ stars, active in last 90 days)
+-------------------+
    |
    | RepoInfo[]
    v
+-------------------+
| 4. Gap Analysis   |  Claude analyzes ecosystem for gaps,
|  (Claude Code)    |  pain themes, and opportunities
+-------------------+
    |
    | GapAnalysis
    v
+-------------------+
| 5. Recommender    |  Combines ontology + tools + gaps
|  (Claude Code)    |  -> Top 5 personalized recommendations
+-------------------+
    |
    | [User selects #N]
    v
+-------------------+
| 6. Data Collector |  Fetches GitHub issues, competitive analysis,
|                   |  integration opportunities, MVP scope
+-------------------+
    |
    | ProjectBrief
    v
+-------------------+
| 7. MVP Builder    |  Claude generates complete working codebase:
|  (Claude Code)    |  Python files, README, tests, Makefile
+-------------------+
    |
    v
  [Runnable MVP in your output directory]
```

---

## Requirements

- Python 3.11+
- [Claude Code](https://claude.ai/download) installed and logged in
- (Optional) `GITHUB_TOKEN` for higher GitHub API rate limits

No `ANTHROPIC_API_KEY` needed. AgentForge uses your Claude Code session directly.

---

## Quick Install

```bash
git clone https://github.com/AlexAI-MCP/AgentForge
cd AgentForge
pip install -e .
```

---

## Quick Start

```bash
# Run the full pipeline (no API key needed!)
agentforge run

# Answer 20 questions, get personalized recommendations, build your MVP
```

That's it. AgentForge handles everything else using your local Claude Code.

---

## Live Demo Output

Real output from AlexLee's profile (A- · 91/100):

```
#1 ConstructIQ Korea   FIT:9.8  MARKET:8.5  Medium  8weeks
   건설 현장의 모든 지식을 AI로 연결하는 건설 특화 GraphRAG 플랫폼

#2 OntologyMe          FIT:9.2  MARKET:7.8  Medium  6weeks
   한국 최초 퍼스널 지식 그래프 SaaS

#3 MCPHub Korea        FIT:8.7  MARKET:8.2  Hard    10weeks
   한국어 MCP 스킬 마켓플레이스

#4 GraphRAG Enterprise FIT:9.0  MARKET:9.0  Hard    12weeks
   한국 기업 문서를 위한 엔터프라이즈 GraphRAG 레이어

#5 AI Community OS     FIT:9.5  MARKET:7.2  Easy    4weeks
   1200명 Discord 커뮤니티를 위한 지식 운영체제
```

---

## Usage

### Full Pipeline

```bash
agentforge run
```

Runs all 6 steps interactively. At step 5 you choose which recommendation to
build. All intermediate results are saved so you can re-run individual steps.

Options:
```
--skip-scan       Skip the local environment scan
--skip-github     Skip GitHub search (use cached results)
--auto-build      Automatically build the top recommendation
```

### Individual Commands

```bash
# Run just the 20-question survey and build your Personal Ontology
agentforge survey

# Scan your local development environment
agentforge scan

# Search GitHub for trending AI repos and run gap analysis
agentforge search
agentforge search --days 60 --limit 15  # custom parameters

# Generate recommendations (requires prior survey)
agentforge recommend

# Build MVP for a specific recommendation
agentforge build 1        # build recommendation #1
agentforge build          # interactive prompt to choose
```

---

## How It Works

### Step 1: Personal Ontology Survey

Twenty questions covering:

| Category | Questions |
|----------|-----------|
| Technical Skills | Primary language, years experience, AI tools used |
| Claude Depth | How deeply you use Claude Code / Anthropic API |
| Domain Expertise | Primary and secondary industry knowledge |
| Pain Points | Biggest workflow frustration + dream tool |
| Availability | Weekly hours, commitment level |
| Strategy | Target user, monetization preference, risk tolerance |
| Context | Team situation, geographic market, open-source stance |
| Motivation | Why you build, past successes, fears, superpower |

Claude then synthesizes these into a **Personal Ontology** — a structured JSON
map of your strengths, gaps, opportunities, builder style, and ideal project
traits.

### Step 2: Environment Scanner

Non-destructive local scan that detects:
- Python packages (pip list)
- Anthropic, OpenAI, LangChain SDKs
- Claude Code skills (~/.claude/skills/)
- MCP server configurations
- VS Code extensions
- npm global packages
- Nearby git repositories
- Available CLI tools (git, docker, node)

### Step 3: GitHub Search

Searches 5 categories across 4 queries each (20 total searches):
- `agent-frameworks` — multi-agent orchestration
- `llm-tools` — prompt engineering, RAG, embeddings
- `automation` — workflow, RPA, computer use
- `developer-tools` — code gen, AI assistants
- `data-pipelines` — vector DBs, knowledge graphs

Returns up to 50 deduplicated repos sorted by stars, filtered to repos
active in the last N days.

### Step 4: Gap Analysis

Claude reads the full repo list and identifies:
- Recurring pain themes in open issues
- "Good but incomplete" frameworks
- High-demand / low-quality-supply areas
- Saturated areas to avoid
- Ranked opportunities with potential scores

### Step 5: Recommendation Engine

Combines all three inputs (ontology + tools + gaps) and Claude generates 5
personalized recommendations, each with:
- Project name and concept
- **Why it fits you specifically** (not generic advice)
- Market opportunity score (1-10)
- Technical difficulty score (1-10)
- Estimated MVP timeline in weeks
- Similar existing projects to differentiate from
- Concrete first steps (immediately actionable)
- Monetization path and risk factors

### Step 6: Data Collector

Once you choose a recommendation:
- Fetches open issues from similar/competing projects
- Classifies issue themes (missing features, bugs, doc gaps)
- Claude synthesizes a detailed **ProjectBrief** including:
  - Precise MVP scope (what to build first)
  - Pain-point evidence from real users
  - Competitive landscape with specific weaknesses
  - Integration opportunities
  - Success metrics
  - Risk/mitigation pairs

### Step 7: MVP Builder

Claude generates a complete, runnable Python project:
- Full package structure with working code
- CLI entry point
- README with setup instructions
- pyproject.toml / requirements.txt
- .env.example
- Makefile
- pytest test suite
- All files written to a timestamped output directory

---

## Architecture

```
agentforge/
├── __init__.py
├── cli.py              Click CLI with 5 commands
├── config.py           Pydantic config, env var loading
├── ontology/
│   ├── survey.py       20-question interactive survey
│   └── builder.py      Claude-powered ontology synthesis
├── scanner/
│   └── tools.py        Local environment scanner
├── github/
│   ├── searcher.py     Async GitHub API client
│   └── analyzer.py     Claude-powered gap analysis
├── recommender/
│   └── engine.py       Personalized recommendation engine
├── collector/
│   └── data.py         GitHub issue research + brief generation
└── mvp/
    └── builder.py      Claude-powered MVP code generation
```

All data flows as typed Pydantic/dataclass objects. Claude is called at 4
stages (ontology, gap analysis, recommendations, MVP generation). All
intermediate outputs are persisted as JSON in `./agentforge_output/` so
individual steps can be re-run without repeating expensive API calls.

---

## Output Files

After a full run, `./agentforge_output/` contains:

```
agentforge_output/
├── survey.json              Your survey answers
├── ontology.json            Your Personal Ontology
├── tool_profile.json        Environment scan results
├── github_repos.json        Fetched GitHub repositories
├── gap_analysis.json        Ecosystem gap analysis
├── recommendations.json     Your 5 recommendations
├── <project>_brief.md       Project brief (Markdown)
├── <project>_brief.json     Project brief (JSON)
└── <project>_YYYYMMDD_HHMMSS/   Generated MVP codebase
    ├── README.md
    ├── pyproject.toml
    ├── requirements.txt
    ├── .env.example
    ├── Makefile
    ├── <package>/
    │   └── *.py
    └── tests/
        └── *.py
```

---

## Configuration

All settings via environment variables or `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `GITHUB_TOKEN` | No | — | GitHub PAT (5000 req/hr vs 60) |
| `AGENTFORGE_MODEL` | No | `claude-opus-4-6` | Claude model to use |
| `AGENTFORGE_OUTPUT_DIR` | No | `./agentforge_output` | Output directory |

Get your Anthropic API key at [console.anthropic.com](https://console.anthropic.com).

Get a GitHub token at [github.com/settings/tokens](https://github.com/settings/tokens)
(no permissions needed — public repo read is sufficient).

---

## Requirements

- Python 3.11+
- `anthropic>=0.40.0`
- `click>=8.1.0`
- `rich>=13.0.0`
- `httpx>=0.27.0`
- `pydantic>=2.0.0`
- `python-dotenv>=1.0.0`
- `jinja2>=3.1.0`

---

## For Korean Developers (한국 개발자를 위한 안내)

AgentForge는 Claude Code를 사용하는 한국 개발자들을 위해 특별히 설계되었습니다.

**설문조사**는 한국어로 진행됩니다 (영어 부제목 포함).

**추천 시스템**은 한국 시장의 특성을 고려합니다:
- 한국어 우선 시장의 기회
- 국내 개발자 커뮤니티의 미충족 수요
- 글로벌 진출을 위한 영어 도구화 전략

AI 에이전트 시대에 무엇을 만들어야 할지 더 이상 고민하지 마세요.
AgentForge가 당신의 강점, 도구, 시장 갭을 분석하여 가장 적합한 프로젝트를 추천합니다.

---

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Run linting (`ruff check . && black --check .`)
6. Submit a pull request

### Development Setup

```bash
git clone https://github.com/agentforge/agentforge
cd agentforge
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env
# Add your API keys to .env
pytest
```

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

## Acknowledgments

Built for Claude Code users who want to spend less time deciding and
more time building. Powered by [Anthropic Claude](https://www.anthropic.com).

---

*AgentForge — Stop deciding. Start building.*
*더 이상 고민하지 말고, 지금 바로 만드세요.*
