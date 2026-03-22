"""
Interactive 20-question personal ontology survey.

Uses Rich for beautiful terminal display. Questions cover technical skills,
domain expertise, tool preferences, pain points, availability, and strategic
orientation — everything needed to build a meaningful personal ontology.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint

console = Console()

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SurveyAnswers:
    """Structured container for all 20 survey responses.

    Attributes:
        q1_primary_language: Primary programming language.
        q2_experience_years: Years of software development experience.
        q3_ai_tools: AI tools currently in daily use.
        q4_claude_usage: How deeply the user uses Claude / Claude Code.
        q5_domain_expertise: Industry domain with deepest expertise.
        q6_second_domain: Secondary domain expertise.
        q7_pain_point: The biggest daily workflow pain point.
        q8_dream_tool: A tool the user wishes existed.
        q9_available_hours: Weekly hours available for a side project.
        q10_commitment_level: Solo project vs startup intention.
        q11_target_user: Who the user most wants to build for.
        q12_monetization: Preferred monetization model.
        q13_risk_tolerance: Financial risk tolerance level.
        q14_team_situation: Current team context.
        q15_geo_market: Primary geographic or language market.
        q16_open_source_stance: Open-source philosophy.
        q17_build_motivation: Core motivation for building things.
        q18_past_project: Description of the most successful past project.
        q19_biggest_fear: Biggest fear about building a new product.
        q20_superpower: Self-assessed unique superpower as a developer.
        raw_responses: Full free-text answers keyed by question number.
    """

    q1_primary_language: str = ""
    q2_experience_years: str = ""
    q3_ai_tools: list[str] = field(default_factory=list)
    q4_claude_usage: str = ""
    q5_domain_expertise: str = ""
    q6_second_domain: str = ""
    q7_pain_point: str = ""
    q8_dream_tool: str = ""
    q9_available_hours: str = ""
    q10_commitment_level: str = ""
    q11_target_user: str = ""
    q12_monetization: str = ""
    q13_risk_tolerance: str = ""
    q14_team_situation: str = ""
    q15_geo_market: str = ""
    q16_open_source_stance: str = ""
    q17_build_motivation: str = ""
    q18_past_project: str = ""
    q19_biggest_fear: str = ""
    q20_superpower: str = ""
    raw_responses: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SurveyAnswers":
        """Deserialize from a plain dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "SurveyAnswers":
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> None:
        """Persist survey answers to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "SurveyAnswers":
        """Load survey answers from a JSON file."""
        return cls.from_json(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Survey questions definition
# ---------------------------------------------------------------------------

QUESTIONS: list[dict[str, Any]] = [
    # 1
    {
        "id": 1,
        "field": "q1_primary_language",
        "title": "Q1. 주력 프로그래밍 언어",
        "subtitle": "What is your primary programming language?",
        "type": "choice",
        "choices": [
            "Python",
            "TypeScript / JavaScript",
            "Go",
            "Rust",
            "Java / Kotlin",
            "C# / .NET",
            "Ruby",
            "기타 (Other)",
        ],
    },
    # 2
    {
        "id": 2,
        "field": "q2_experience_years",
        "title": "Q2. 개발 경력",
        "subtitle": "How many years have you been writing code professionally?",
        "type": "choice",
        "choices": [
            "1년 미만 (< 1 year)",
            "1–3년 (1–3 years)",
            "3–5년 (3–5 years)",
            "5–10년 (5–10 years)",
            "10년 이상 (10+ years)",
        ],
    },
    # 3
    {
        "id": 3,
        "field": "q3_ai_tools",
        "title": "Q3. 현재 사용 중인 AI 도구",
        "subtitle": "Which AI tools do you use regularly? (여러 개 선택 가능 — enter numbers separated by commas)",
        "type": "multi_choice",
        "choices": [
            "Claude / Claude Code",
            "ChatGPT / OpenAI API",
            "GitHub Copilot",
            "Cursor",
            "Windsurf",
            "Gemini / Google AI",
            "Local LLM (Ollama, LM Studio 등)",
            "기타 (Other)",
        ],
    },
    # 4
    {
        "id": 4,
        "field": "q4_claude_usage",
        "title": "Q4. Claude Code 활용 깊이",
        "subtitle": "How deeply do you use Claude Code or the Anthropic API?",
        "type": "choice",
        "choices": [
            "처음 써봄 — 방금 시작했어요 (Just starting out)",
            "기본 채팅 사용 (Basic chat only)",
            "Claude Code로 코딩 보조 (Coding assistant via Claude Code)",
            "API 직접 통합 (Direct API integration in projects)",
            "멀티에이전트 파이프라인 구축 중 (Building multi-agent pipelines)",
        ],
    },
    # 5
    {
        "id": 5,
        "field": "q5_domain_expertise",
        "title": "Q5. 가장 깊은 도메인 전문성",
        "subtitle": "Which industry or domain do you know best?",
        "type": "choice",
        "choices": [
            "SaaS / B2B 소프트웨어",
            "핀테크 / 금융 (Fintech / Finance)",
            "헬스케어 / 의료 (Healthcare)",
            "이커머스 / 리테일 (E-commerce / Retail)",
            "교육 / EdTech",
            "부동산 / 건설 (Real estate / Construction)",
            "미디어 / 콘텐츠 (Media / Content)",
            "제조 / 물류 (Manufacturing / Logistics)",
            "법률 / 컴플라이언스 (Legal / Compliance)",
            "개발자 도구 / 인프라 (Dev tools / Infrastructure)",
            "기타 (Other)",
        ],
    },
    # 6
    {
        "id": 6,
        "field": "q6_second_domain",
        "title": "Q6. 두 번째 도메인 전문성",
        "subtitle": "Secondary domain where you also have meaningful experience?",
        "type": "choice",
        "choices": [
            "없음 (None — I focus on one)",
            "SaaS / B2B 소프트웨어",
            "핀테크 / 금융",
            "헬스케어 / 의료",
            "이커머스 / 리테일",
            "교육 / EdTech",
            "부동산 / 건설",
            "미디어 / 콘텐츠",
            "데이터 / AI / ML",
            "개발자 도구 / 인프라",
            "기타 (Other)",
        ],
    },
    # 7
    {
        "id": 7,
        "field": "q7_pain_point",
        "title": "Q7. 가장 큰 업무 고통",
        "subtitle": "What is the single biggest pain point in your daily workflow?",
        "type": "choice",
        "choices": [
            "반복적인 코드 / 보일러플레이트 작성 (Repetitive boilerplate)",
            "문서 작성과 유지관리 (Writing & maintaining docs)",
            "데이터 수집 및 전처리 (Data collection & preprocessing)",
            "API 통합과 glue 코드 (API integrations & glue code)",
            "테스트 작성 (Writing tests)",
            "코드 리뷰와 품질 관리 (Code review & quality)",
            "배포 및 인프라 관리 (Deployment & infra management)",
            "아이디어→실제 구현 격차 (Idea-to-implementation gap)",
            "팀 커뮤니케이션 / 동기화 (Team communication & sync)",
            "고객 피드백 수집 및 분석 (Customer feedback collection)",
        ],
    },
    # 8
    {
        "id": 8,
        "field": "q8_dream_tool",
        "title": "Q8. 있었으면 하는 도구",
        "subtitle": "If you could magically create one tool that doesn't exist yet, what would it do? (자유 입력)",
        "type": "free_text",
    },
    # 9
    {
        "id": 9,
        "field": "q9_available_hours",
        "title": "Q9. 사이드 프로젝트 가용 시간",
        "subtitle": "How many hours per week can you realistically dedicate to a new project?",
        "type": "choice",
        "choices": [
            "5시간 미만 (< 5 hrs)",
            "5–10시간 (5–10 hrs)",
            "10–20시간 (10–20 hrs)",
            "20–40시간 (20–40 hrs — near full-time)",
            "풀타임 (Full-time — 40h+)",
        ],
    },
    # 10
    {
        "id": 10,
        "field": "q10_commitment_level",
        "title": "Q10. 커밋 수준 & 목표",
        "subtitle": "What is your intention for this project?",
        "type": "choice",
        "choices": [
            "개인 자동화 / 내부 도구 (Personal automation / internal tool)",
            "오픈소스로 커뮤니티 기여 (Open-source community contribution)",
            "사이드 프로젝트 수익화 (Side project monetization)",
            "스타트업 론칭 (Launching a startup)",
            "현재 직장 내 혁신 프로젝트 (Innovation project at current job)",
        ],
    },
    # 11
    {
        "id": 11,
        "field": "q11_target_user",
        "title": "Q11. 타겟 사용자",
        "subtitle": "Who do you most want to build for?",
        "type": "choice",
        "choices": [
            "나 자신 (Myself — dogfooding)",
            "개발자 / 엔지니어 (Developers / Engineers)",
            "AI 파워유저 (AI power users — Claude Code, etc.)",
            "스타트업 창업자 (Startup founders)",
            "중소기업 오너 (SMB owners)",
            "대기업 직원 / 팀 (Enterprise employees / teams)",
            "일반 소비자 (General consumers)",
            "특정 직종 전문가 (Domain professionals — doctors, lawyers, etc.)",
        ],
    },
    # 12
    {
        "id": 12,
        "field": "q12_monetization",
        "title": "Q12. 수익화 선호도",
        "subtitle": "How do you prefer to monetize what you build?",
        "type": "choice",
        "choices": [
            "오픈소스 (수익화 불필요) (Open source — no monetization needed)",
            "오픈코어 (무료 + 유료 기능) (Open-core — free + paid features)",
            "SaaS 구독 (SaaS subscription)",
            "사용량 기반 과금 (Usage-based pricing)",
            "일회성 구매 / 라이선스 (One-time purchase / license)",
            "컨설팅 / 서비스 (Consulting / services built on the tool)",
            "아직 미정 (Undecided)",
        ],
    },
    # 13
    {
        "id": 13,
        "field": "q13_risk_tolerance",
        "title": "Q13. 리스크 허용도",
        "subtitle": "What is your financial risk tolerance for this project?",
        "type": "choice",
        "choices": [
            "제로 리스크 — 본업 유지하며 진행 (Zero risk — keep day job)",
            "낮음 — 월 $100 이하 비용 감당 가능 (Low — up to $100/mo costs)",
            "중간 — 월 $500 이하, 6개월 시도 (Medium — $500/mo, 6mo runway)",
            "높음 — 1년 이상 런웨이 보유 (High — 1yr+ personal runway)",
            "올인 — 이미 퇴사 또는 결정됨 (All-in — already quit or decided)",
        ],
    },
    # 14
    {
        "id": 14,
        "field": "q14_team_situation",
        "title": "Q14. 팀 상황",
        "subtitle": "What is your current team situation?",
        "type": "choice",
        "choices": [
            "완전 솔로 (Completely solo)",
            "파트타임 코파운더 있음 (Have a part-time co-founder)",
            "풀타임 코파운더 있음 (Have a full-time co-founder)",
            "소규모 팀 (2–5명) (Small team 2–5 people)",
            "기업 내 팀 프로젝트 (Corporate team project)",
        ],
    },
    # 15
    {
        "id": 15,
        "field": "q15_geo_market",
        "title": "Q15. 지리적 / 언어 시장",
        "subtitle": "What is your primary target market geography or language?",
        "type": "choice",
        "choices": [
            "한국 (Korea — Korean language first)",
            "글로벌 영어권 (Global English-speaking markets)",
            "일본 (Japan)",
            "동남아시아 (Southeast Asia)",
            "유럽 (Europe)",
            "북미 (North America)",
            "글로벌 (No specific focus — global from day 1)",
        ],
    },
    # 16
    {
        "id": 16,
        "field": "q16_open_source_stance",
        "title": "Q16. 오픈소스 철학",
        "subtitle": "What is your open-source philosophy?",
        "type": "choice",
        "choices": [
            "모든 것을 오픈소스로 공개해야 함 (Everything should be open source)",
            "핵심 도구는 오픈소스, 서비스로 수익화 (Core open, monetize services)",
            "소스는 닫혀 있되 공정한 라이선스 (Closed but fair licensing)",
            "완전 독점 소프트웨어 선호 (Prefer fully proprietary)",
            "상황에 따라 다름 (Depends on the project)",
        ],
    },
    # 17
    {
        "id": 17,
        "field": "q17_build_motivation",
        "title": "Q17. 빌딩 동기",
        "subtitle": "What is your core motivation for building things?",
        "type": "choice",
        "choices": [
            "내 문제를 내가 해결하고 싶어서 (Scratch my own itch)",
            "기술적 챌린지 자체가 즐거워서 (Technical challenge is fun)",
            "경제적 자유를 얻고 싶어서 (Financial freedom)",
            "세상에 영향을 미치고 싶어서 (Make an impact on the world)",
            "커뮤니티/생태계에 기여하고 싶어서 (Contribute to community)",
            "이력서/포트폴리오 강화 (Build portfolio / resume)",
            "AI와 함께 무엇이 가능한지 탐구 (Explore what's possible with AI)",
        ],
    },
    # 18
    {
        "id": 18,
        "field": "q18_past_project",
        "title": "Q18. 가장 성공적인 과거 프로젝트",
        "subtitle": "Briefly describe your most successful personal or professional project. What made it succeed? (자유 입력)",
        "type": "free_text",
    },
    # 19
    {
        "id": 19,
        "field": "q19_biggest_fear",
        "title": "Q19. 새 제품 빌딩의 가장 큰 두려움",
        "subtitle": "What is your biggest fear about starting a new product?",
        "type": "choice",
        "choices": [
            "아무도 안 쓸 것 같아서 (No one will use it)",
            "이미 더 나은 게 있을 것 같아서 (It already exists and is better)",
            "만드는 데 너무 오래 걸릴 것 같아서 (Will take too long to build)",
            "기술 스택 선택이 잘못될 것 같아서 (Wrong tech stack choice)",
            "마케팅을 못 할 것 같아서 (Can't do marketing)",
            "혼자 하기엔 너무 복잡해서 (Too complex to do alone)",
            "시장 타이밍이 맞지 않을 것 같아서 (Bad market timing)",
            "수익화에 실패할 것 같아서 (Will fail to monetize)",
        ],
    },
    # 20
    {
        "id": 20,
        "field": "q20_superpower",
        "title": "Q20. 나의 개발자 슈퍼파워",
        "subtitle": "What is your unique superpower as a developer? What do you do faster or better than most people? (자유 입력)",
        "type": "free_text",
    },
]


# ---------------------------------------------------------------------------
# Survey runner
# ---------------------------------------------------------------------------


class SurveyRunner:
    """Runs the interactive 20-question personal ontology survey.

    Uses Rich for styled terminal output. Supports resuming from a partially
    completed survey saved to disk.

    Args:
        save_path: Path where survey answers are automatically saved after
            each question. Allows resuming interrupted sessions.
    """

    def __init__(self, save_path: Path | None = None) -> None:
        self.save_path = save_path
        self.answers = SurveyAnswers()

    def run(self) -> SurveyAnswers:
        """Execute the full survey interactively.

        Returns:
            Completed SurveyAnswers with all 20 responses.
        """
        self._print_intro()

        for question in QUESTIONS:
            self._ask_question(question)
            if self.save_path:
                self.answers.save(self.save_path)

        self._print_outro()
        return self.answers

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_intro(self) -> None:
        console.print()
        console.print(
            Panel.fit(
                Text.from_markup(
                    "[bold cyan]AgentForge[/] — Personal Ontology Survey\n\n"
                    "[dim]20개의 질문으로 당신만의 빌딩 청사진을 만듭니다.[/]\n"
                    "[dim]20 questions to map your unique builder DNA.[/]\n\n"
                    "[yellow]약 5–8분 소요됩니다. (Approx 5–8 minutes)[/]"
                ),
                title="[bold]Welcome / 환영합니다[/]",
                border_style="cyan",
            )
        )
        console.print()

    def _print_outro(self) -> None:
        console.print()
        console.print(
            Panel.fit(
                "[bold green]설문 완료! Survey complete![/]\n\n"
                "이제 당신의 Personal Ontology를 생성합니다.\n"
                "Building your Personal Ontology now...",
                border_style="green",
            )
        )
        console.print()

    def _ask_question(self, question: dict) -> None:
        """Render and collect a single question."""
        q_id: int = question["id"]
        q_type: str = question["type"]

        console.print(Rule(f"[bold]{question['title']}[/] ({q_id}/20)", style="dim"))
        console.print(f"  [italic dim]{question['subtitle']}[/]")
        console.print()

        if q_type == "choice":
            answer = self._ask_single_choice(question["choices"])
        elif q_type == "multi_choice":
            answer = self._ask_multi_choice(question["choices"])
        else:  # free_text
            answer = self._ask_free_text()

        # Store in the right field
        field_name: str = question["field"]
        if field_name == "q3_ai_tools":
            object.__setattr__(self.answers, field_name, answer if isinstance(answer, list) else [answer])
        else:
            object.__setattr__(self.answers, field_name, answer if isinstance(answer, str) else str(answer))

        self.answers.raw_responses[f"q{q_id}"] = (
            ", ".join(answer) if isinstance(answer, list) else answer
        )
        console.print()

    def _ask_single_choice(self, choices: list[str]) -> str:
        """Display numbered choices and return the selected text."""
        for i, choice in enumerate(choices, 1):
            console.print(f"  [cyan]{i:>2}.[/] {choice}")
        console.print()

        while True:
            raw = Prompt.ask(
                "  [bold]선택 (Enter number)[/]",
                console=console,
            )
            try:
                idx = int(raw.strip()) - 1
                if 0 <= idx < len(choices):
                    selected = choices[idx]
                    console.print(f"  [green]선택됨:[/] {selected}")
                    return selected
            except ValueError:
                pass
            console.print("  [red]유효한 번호를 입력하세요 (Enter a valid number)[/]")

    def _ask_multi_choice(self, choices: list[str]) -> list[str]:
        """Display numbered choices and return a list of selected texts."""
        for i, choice in enumerate(choices, 1):
            console.print(f"  [cyan]{i:>2}.[/] {choice}")
        console.print()

        while True:
            raw = Prompt.ask(
                "  [bold]선택 (Comma-separated numbers, e.g. 1,3,5)[/]",
                console=console,
            )
            try:
                indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
                if indices and all(0 <= i < len(choices) for i in indices):
                    selected = [choices[i] for i in indices]
                    console.print(f"  [green]선택됨:[/] {', '.join(selected)}")
                    return selected
            except ValueError:
                pass
            console.print("  [red]유효한 번호를 콤마로 구분하여 입력하세요[/]")

    def _ask_free_text(self) -> str:
        """Collect a free-text answer."""
        answer = Prompt.ask("  [bold]답변[/]", console=console)
        while not answer.strip():
            console.print("  [red]답변을 입력해주세요 (Please enter an answer)[/]")
            answer = Prompt.ask("  [bold]답변[/]", console=console)
        return answer.strip()
