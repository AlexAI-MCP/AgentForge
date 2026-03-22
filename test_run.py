"""
AgentForge 실제 파이프라인 테스트 — AlexLee 온톨로지 기반
API 키 없이 로컬 claude CLI 사용
"""
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from agentforge.llm import ask_json
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

console = Console(force_terminal=True, highlight=False)

# ── Step 1: Load existing ontology ──────────────────────────────────────────
console.print(Panel("[bold cyan]STEP 1: 개인 온톨로지 로드[/]", expand=False))
ontology = json.loads(Path("agentforge_output/ontology.json").read_text(encoding="utf-8"))
console.print(f"[green]✓[/] {ontology['name']} 온톨로지 로드 완료 (점수: {ontology['overall_score']}점 {ontology['grade']})")
console.print(f"  강점: {', '.join(ontology['strengths'][:3])}")

# ── Step 2: Env scan summary ─────────────────────────────────────────────────
console.print(Panel("[bold cyan]STEP 2: 로컬 환경 스캔[/]", expand=False))
console.print("[green]✓[/] AI 패키지: anthropic 0.79, neo4j 6.1, langchain 1.2, chromadb 1.4, torch 2.12 (CUDA)")
console.print("[green]✓[/] MCP 서버: neo4j · notebooklm · obsidian · apify · blender · paper-search")
console.print("[green]✓[/] Git 프로젝트: AgentForge · Ontology · ChatMock · trustgraph · Stock")

# ── Step 3: GitHub gap summary ───────────────────────────────────────────────
console.print(Panel("[bold cyan]STEP 3: GitHub 생태계 갭 분석[/]", expand=False))
console.print("[green]✓[/] LangChain (130K★) — 한국어 없음, 개인 온톨로지 개념 없음")
console.print("[green]✓[/] cognee (14K★) — 한국 시장 없음, 건설 도메인 없음")
console.print("[green]✓[/] reor (8.5K★) — 그래프 시각화 없음, 에이전트 미통합")
console.print("[green]✓[/] OrbitOS (634★) — 미완성, 한국어 미지원")

# ── Step 4: Claude recommendations ──────────────────────────────────────────
console.print(Panel("[bold cyan]STEP 4: Claude 맞춤 추천 생성 중...[/]", expand=False))

prompt = """You are an expert product strategist for AI developers. Based on the profile and ecosystem gaps below, generate exactly 5 personalized project recommendations as a JSON array.

## Developer Profile (AlexLee)
- Korean, age 40, 19 years construction/landscape architecture
- Community leader: 1,200-member Korean AI Creators Assoc co-chair, Kakao AI Ambassador, YouTube 10K
- Technical stack: Claude Code (127 sub-agents), Neo4j, Graph RAG, ChromaDB, LangChain, Remotion video generation, Discord bots, MCP servers, CUDA/PyTorch
- Domain expertise: construction/real estate, Korean B2B enterprise, AI education, content creation
- Vision: Korea's Palantir — Intelligence OS platform
- Primary pain: helping people (and himself) decide what to build in the agent era
- Constraint: family financial security, target $6K MRR before leaving day job

## GitHub Ecosystem Gaps
- No Korean personal ontology builder (all tools are English-first)
- No construction/real estate + AI knowledge platform in Korea
- No "what should I build" advisor with personal context + GitHub analysis
- No MCP skill marketplace (skills scattered, no curation layer)
- cognee/reor are good but incomplete — no Korean support, no construction domain
- AgentForge itself is being built (what else?)

## Return ONLY this JSON array (no markdown, no explanation):
[
  {
    "rank": 1,
    "name": "ProjectName",
    "tagline_ko": "한국어 한줄 설명",
    "tagline_en": "English one-liner",
    "why_you": "Why AlexLee specifically (2 sentences)",
    "market_gap": "What is missing in ecosystem",
    "tech_stack": ["tech1", "tech2", "tech3"],
    "mvp_features": ["feature1", "feature2", "feature3"],
    "revenue_model": "How to monetize",
    "difficulty": "Easy|Medium|Hard",
    "market_score": 8.5,
    "fit_score": 9.0,
    "mvp_weeks": 4,
    "korean_edge": "Korean market advantage"
  }
]"""

recs = ask_json(prompt)

# Save
Path("agentforge_output").mkdir(exist_ok=True)
Path("agentforge_output/recommendations.json").write_text(
    json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Display
table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
table.add_column("#", width=3)
table.add_column("프로젝트", width=22)
table.add_column("핏", width=5)
table.add_column("시장", width=5)
table.add_column("난이도", width=8)
table.add_column("MVP", width=6)
table.add_column("한국어 태그라인", width=35)

for r in recs:
    table.add_row(
        str(r["rank"]),
        f"[bold]{r['name']}[/]",
        f"[green]{r['fit_score']}[/]",
        f"[cyan]{r['market_score']}[/]",
        r["difficulty"],
        f"{r['mvp_weeks']}주",
        r["tagline_ko"],
    )

console.print(table)
console.print()

for r in recs:
    console.print(Panel(
        f"[bold yellow]{r['name']}[/] — {r['tagline_en']}\n\n"
        f"[bold]WHY YOU:[/] {r['why_you']}\n\n"
        f"[bold]갭:[/] {r['market_gap']}\n\n"
        f"[bold]MVP 기능:[/] " + " | ".join(r.get('mvp_features', [])) + "\n\n"
        f"[bold]수익화:[/] {r['revenue_model']}\n\n"
        f"[bold]한국 어드밴티지:[/] {r['korean_edge']}\n\n"
        f"[bold]Tech:[/] {', '.join(r.get('tech_stack', []))}",
        title=f"[bold]#{r['rank']}[/]",
        border_style="cyan" if r["rank"] == 1 else "dim",
    ))

console.print("\n[bold green]✓ agentforge_output/recommendations.json 저장 완료[/]")
console.print("[dim]다음: agentforge build <번호> 로 MVP 생성[/]")
