"""Whole-document reading plans, evidence and generated executable artifacts."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Chapter(Strict):
    id:str
    title:str
    node_ids:list[str]=Field(min_length=1)
    takeaway:str
    interaction:str
    changes:str
    basis:Literal['paper','teaching','structure','mixed']
    sources:list[str]=Field(min_length=1)
    acceptance:str

class ReadingPlan(Strict):
    title:str
    thesis:str
    art_direction:str
    reading_path:str
    chapters:list[Chapter]=Field(min_length=3,max_length=9)
    visual_pages:list[int]=Field(max_length=4)
    boundaries:list[str]

class EvidenceRow(Strict):
    id:str
    label:str
    values:dict[str,str|None]

class EvidenceTable(Strict):
    id:str
    title:str
    population:str
    columns:list[str]
    rows:list[EvidenceRow]
    notes:list[str]

    @model_validator(mode='after')
    def unique_columns(self):
        if len(set(self.columns))!=len(self.columns):raise ValueError('多级表头必须展开成唯一列名，禁止字典覆盖语言/年份列')
        if len({r.id for r in self.rows})!=len(self.rows):raise ValueError('表格行ID重复')
        if any(set(r.values)-set(self.columns) for r in self.rows):raise ValueError('表格字段不属于原表列')
        return self

class PageEvidence(Strict):
    page:int
    tables:list[EvidenceTable]
    observations:list[str]
    uncertainties:list[str]

class ReadingArtifact(Strict):
    title:str
    description:str
    html:str=Field(max_length=150000)
    css:str=Field(max_length=100000)
    javascript:str=Field(max_length=90000)
    teaching_assumptions:list[str]
    limitations:list[str]

class Finding(Strict):
    severity:Literal['blocker','minor']
    location:str
    detail:str

class ReadingReview(Strict):
    verdict:Literal['pass','revise']
    findings:list[Finding]
    coverage:list[str]
