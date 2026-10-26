from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class Output(BaseModel):
    model_config = ConfigDict(extra='forbid')

class PlanNode(Output):
    id: str
    title: str
    purpose: str
    source_pages: list[int] = Field(min_length=1)
    required: bool

class Plan(Output):
    title: str
    subtitle: str
    domain: str
    nodes: list[PlanNode] = Field(min_length=3,max_length=14)
    coverage_notes: list[str]
    core_gaps: list[str]

class Claim(Output):
    id: str
    statement: str
    conditions: list[str]
    source_ids: list[str] = Field(min_length=1)

class Step(Output):
    title: str
    text: str
    source_ids: list[str]

class Term(Output):
    id: str
    title: str
    layer: str
    lead: str
    text: str
    why: str
    source_ids: list[str]

class LessonNode(Output):
    id: str
    title: str
    summary: str
    paragraphs: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    claims: list[Claim] = Field(min_length=1)
    interaction: Literal['none','stepper']
    steps: list[Step]
    terms: list[Term]
    formula: str | None
    assumptions: list[str]

class NodeBatch(Output):
    nodes: list[LessonNode]

class ReviewItem(Output):
    node_id: str
    verdict: Literal['supported','insufficient','contradicted']
    issues: list[str]
    unsupported_claim_ids: list[str]

class Review(Output):
    items: list[ReviewItem]

class Visual(Output):
    page: int
    description: str
    chart_or_table: bool
    formulas: list[str]
    extracted_data: list[str]
    limitations: list[str]

class Answer(Output):
    text: str
    source_ids: list[str]
    need_external: bool
    search_query: str | None
    action: Literal['none','next_step','previous_step','reset_steps']
    memory_preference: str | None

class AnswerReview(Output):
    verdict: Literal['supported','insufficient','contradicted']
    issues: list[str]

class Knowledge(Output):
    title: str
    layer: str
    lead: str
    text: str
    why: str
    source_ids: list[str]
    next_question: str

class SearchQuery(Output):
    query: str = Field(min_length=3,max_length=180)

class CopilotResearchPlan(Output):
    objective: str = Field(min_length=3,max_length=500)
    questions: list[str] = Field(min_length=1,max_length=4)
    use_attached_documents: bool
    use_external_sources: bool
    answer_format: Literal['explanation','comparison','critical_review','research_note']

class Coverage(Output):
    verdict: Literal['covered','gaps']
    gaps: list[str]

class PageDigest(Output):
    page: int
    summary: str
    important_source_ids: list[str]

class Digests(Output):
    pages: list[PageDigest]
