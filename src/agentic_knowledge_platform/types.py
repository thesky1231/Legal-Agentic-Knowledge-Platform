from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from typing import Literal


QuestionType = Literal[
    "direct_answer",
    "definition",
    "confusing",
    "complex_reasoning",
    "should_refuse",
]


@dataclass(slots=True)
class DocumentIngestRequest:
    title: str
    content: str
    source: str = "manual"
    modality: str = "markdown"
    language: str = "zh"
    tenant_id: str = "default"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedElement:
    kind: str
    content: str
    section: str
    page: int = 1
    metadata: dict[str, str | int] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    document_id: str
    title: str
    source: str
    modality: str
    language: str
    outline: list[str]
    elements: list[ParsedElement]
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    document_id: str
    title: str
    section: str
    content: str
    source: str
    metadata: dict[str, str] = field(default_factory=dict)
    token_count: int = 0


@dataclass(slots=True)
class Citation:
    document_id: str
    chunk_id: str
    title: str
    section: str
    snippet: str
    score: float


@dataclass(slots=True)
class RetrievalHit:
    chunk: ChunkRecord
    vector_score: float
    rerank_score: float
    final_score: float


@dataclass(slots=True)
class AnswerSection:
    title: str
    body: str


@dataclass(slots=True)
class AnswerResult:
    answer: str
    grounded: bool
    citations: list[Citation]
    answer_sections: list[AnswerSection] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    question_type: QuestionType = "direct_answer"
    confidence: str = "medium"
    refusal_triggered: bool = False


@dataclass(slots=True)
class ModelRequest:
    task: str
    prompt: str
    context_blocks: list[str] = field(default_factory=list)
    session_id: str = "default"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ModelResponse:
    model: str
    route: str
    output: str
    latency_ms: int
    diagnostics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentRequest:
    query: str
    session_id: str = "default"
    speak_response: bool = False
    tenant_id: str = "default"


@dataclass(slots=True)
class AgentStep:
    index: int
    agent: str
    thought: str
    action: str
    observation: str


@dataclass(slots=True)
class VoiceJob:
    job_id: str
    voice: str
    text: str
    script: str
    audio_url: str
    avatar_job_id: str
    avatar_status: str
    estimated_latency_ms: int


@dataclass(slots=True)
class AgentResponse:
    answer: str
    grounded: bool
    citations: list[Citation]
    steps: list[AgentStep]
    answer_sections: list[AnswerSection] = field(default_factory=list)
    voice_job: VoiceJob | None = None
    agent_mode: str = "single"
    review_summary: str | None = None
    run_id: str | None = None
    question_type: QuestionType = "direct_answer"
    confidence: str = "medium"
    refusal_triggered: bool = False


@dataclass(slots=True)
class IngestionResult:
    document: ParsedDocument
    chunks: list[ChunkRecord]


@dataclass(slots=True)
class WorkflowRun:
    document_id: str
    chunk_count: int
    agent_response: AgentResponse


@dataclass(slots=True)
class RunRecord:
    run_id: str
    workflow: str
    agent_mode: str
    session_id: str
    tenant_id: str
    query: str
    grounded: bool
    citation_count: int
    answer_preview: str
    created_at: datetime
    review_summary: str | None = None


@dataclass(slots=True)
class EvalCase:
    case_id: str
    tenant_id: str
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    min_citations: int = 1
    agent_mode: str = "single"
    expected_question_type: str | None = None
    should_refuse: bool | None = None
    expected_articles: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EvalCaseResult:
    case_id: str
    tenant_id: str
    grounded: bool
    citation_count: int
    keyword_hit_rate: float
    passed: bool
    latency_ms: int
    answer_preview: str
    question_type: str = "direct_answer"
    confidence: str = "medium"
    question_type_match: bool = True
    refusal_match: bool = True
    citation_match: bool = True
    policy_passed: bool = True


@dataclass(slots=True)
class EvalRun:
    dataset_name: str
    case_count: int
    grounded_rate: float
    citation_coverage_rate: float
    pass_rate: float
    avg_latency_ms: int
    results: list[EvalCaseResult]
    question_type_match_rate: float = 0.0
    refusal_match_rate: float = 0.0
    citation_match_rate: float = 0.0
    policy_pass_rate: float = 0.0
