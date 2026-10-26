from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ChatRequest(StrictModel):
    text: str = Field(min_length=1, max_length=6000)
    node_id: str
    selected_text: str | None = Field(default=None, max_length=2000)
    selected_page: int | None = Field(default=None,ge=1)
    bbox: list[float] | None = Field(default=None,min_length=4,max_length=4)
    current_step: int = Field(default=0,ge=0)

class CopilotRunRequest(ChatRequest):
    mode: Literal['auto','quick','deep'] = 'auto'

class CopilotDecision(StrictModel):
    action: Literal['approve_plan','revise_plan','cancel']
    comment: str | None = Field(default=None,max_length=2000)

class PatchRequest(StrictModel):
    message_id: str
    base_revision: int = Field(ge=1)

class RevisionRequest(StrictModel):
    base_revision: int = Field(ge=1)

class ConceptRequest(StrictModel):
    document_id: str
    concept_id: str = Field(min_length=1,max_length=150)

class GenerationRequest(StrictModel):
    force_ocr_pages: list[int] = Field(default_factory=list,max_length=120)

class KnowledgeRequest(StrictModel):
    concept_id: str
    question: str | None = Field(default=None,max_length=2000)

class ActionResult(StrictModel):
    status: Literal['executed','rejected']
    detail: str = Field(max_length=200)

class AttachmentRequest(StrictModel):
    document_id: str

class DemoAction(StrictModel):
    type: Literal["set_search_scope"]
    scope: Literal["all", "local", "narrow"]
    node_id: Literal["mechanism"]
