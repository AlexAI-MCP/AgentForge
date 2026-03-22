"""Run AgentForge recommendation pipeline — no API key needed."""
import json
import sys
from pathlib import Path

# Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agentforge.llm import ask_json

ontology = json.loads(Path("agentforge_output/ontology.json").read_text(encoding="utf-8"))
print(f"[OK] Ontology: {ontology['name']} {ontology['grade']} ({ontology['overall_score']}pts)")

PROMPT = (
    "Korean AI developer profile: age 40, 19yr construction background, "
    "community leader 1200 AI assoc members, tech stack Claude Code + Neo4j + GraphRAG + Remotion + Discord + MCP + PyTorch CUDA, "
    "vision Korea Palantir, goal $6K MRR. "
    "Ecosystem gaps: no Korean personal ontology builder, no construction+AI platform, no MCP skill marketplace, no Korean GraphRAG enterprise layer. "
    "Generate 5 product ideas for this developer (NOT AgentForge itself). "
    "Return a JSON array of 5 objects. Each object must have exactly these keys: "
    "rank (1-5), name (str), tagline_ko (Korean str), tagline_en (English str), "
    "why_you (str), market_gap (str), tech_stack (list of str), mvp_features (list of 3 str), "
    "revenue_model (str), difficulty (Easy or Medium or Hard), "
    "market_score (float 1-10), fit_score (float 1-10), mvp_weeks (int), korean_edge (str). "
    "Return ONLY the JSON array, no other text."
)

print("Calling Claude for recommendations...")
recs = ask_json(PROMPT)

if isinstance(recs, dict):
    recs = list(recs.values()) if recs else []

Path("agentforge_output/recommendations.json").write_text(
    json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("\n" + "=" * 65)
print("  AGENTFORGE — AlexLee 맞춤 추천 TOP 5")
print("=" * 65)

for r in recs:
    print(f"\n#{r['rank']} {r['name']}")
    print(f"  KO: {r.get('tagline_ko', '')}")
    print(f"  EN: {r.get('tagline_en', '')}")
    print(f"  FIT: {r.get('fit_score','?')}/10  |  MARKET: {r.get('market_score','?')}/10  |  DIFF: {r.get('difficulty','?')}  |  MVP: {r.get('mvp_weeks','?')}weeks")
    print(f"  WHY: {str(r.get('why_you', ''))[:120]}")
    print(f"  GAP: {str(r.get('market_gap', ''))[:100]}")
    print(f"  MVP: {' | '.join(r.get('mvp_features', []))}")
    print(f"  REVENUE: {r.get('revenue_model', '')}")
    print(f"  TECH: {', '.join(r.get('tech_stack', []))}")
    print(f"  KR EDGE: {str(r.get('korean_edge', ''))[:100]}")

print(f"\n[OK] Saved to agentforge_output/recommendations.json")
print("Next: python run_mvp.py <rank_number>")
