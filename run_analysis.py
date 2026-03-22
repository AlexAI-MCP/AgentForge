import anthropic, json

client = anthropic.Anthropic()

prompt = """You are an expert product strategist. Based on the personal ontology and GitHub ecosystem analysis below, generate TOP 5 personalized project recommendations in JSON.

## Personal Ontology (AlexLee)
- Background: 19 years construction/landscape architecture + AI ecosystem builder
- 8-Space Score: A- (91/100) — Clustering 9.0, Semantic 8.5, Causal 8.5, Structural 8.0
- Tools: Claude Code + 127 sub-agents, Neo4j, ChromaDB, LangChain, Graph RAG, Remotion, Discord Bot, MCP servers
- Installed: anthropic 0.79, neo4j 6.1, langchain 1.2, chromadb 1.4, torch 2.12 CUDA, transformers 4.57
- MCP Servers: neo4j, notebooklm-mcp, obsidian, apify, blender, paper-search
- Community: Co-chair Korean AI Creators Assoc (1,200 members), Kakao AI Ambassador, YouTube 10K
- Domain: Construction, Korean enterprise B2B, AI education, content creation
- Vision: Korea's Palantir — Intelligence OS
- Constraint: Family financial security, exit trigger $6K MRR
- Pain: Decision paralysis about what to build in agent era

## GitHub Ecosystem Gaps
- LangChain 130K stars: Too complex, no Korean localization, no personal ontology
- cognee 14K stars: Knowledge engine but no Korean market, no construction angle
- reor 8.5K stars: Local AI knowledge mgmt but no graph viz, no agent integration
- OrbitOS 634 stars: AI productivity but incomplete, no Korean support
- GraphRAG: Good but no personal ontology layer, no Korean enterprise use case

## Key Market Gaps:
1. No Korean-language personal ontology builder
2. No construction/real estate + AI knowledge platform
3. No "what should I build" AI advisor with personal context
4. No MCP skill marketplace or curation layer
5. No Graph RAG with Korean enterprise + personal context

Return ONLY a valid JSON array of 5 recommendations:
[
  {
    "rank": 1,
    "name": "Project Name",
    "tagline": "One-line pitch in Korean + English",
    "why_you": "Why this fits AlexLee specifically",
    "market_gap": "What is missing in the ecosystem",
    "tech_stack": ["tech1", "tech2"],
    "mvp_scope": "MVP includes: 1) X  2) Y  3) Z",
    "revenue_model": "How to monetize",
    "difficulty": "Easy or Medium or Hard",
    "market_score": 8.5,
    "fit_score": 9.0,
    "korean_advantage": "Why Korean market is perfect entry point"
  }
]"""

msg = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4000,
    messages=[{"role": "user", "content": prompt}]
)

text = msg.content[0].text.strip()
if "```" in text:
    text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]

recs = json.loads(text.strip())

# Save
with open("agentforge_output/recommendations.json", "w", encoding="utf-8") as f:
    json.dump(recs, f, ensure_ascii=False, indent=2)

# Pretty print
for r in recs:
    print(f"\n{'='*60}")
    print(f"#{r['rank']} {r['name']}")
    print(f"   {r['tagline']}")
    print(f"   핏 점수: {r['fit_score']}/10  |  시장 점수: {r['market_score']}/10  |  난이도: {r['difficulty']}")
    print(f"   WHY YOU: {r['why_you']}")
    print(f"   MVP: {r['mvp_scope']}")
    print(f"   수익화: {r['revenue_model']}")
    print(f"   한국 어드밴티지: {r['korean_advantage']}")
