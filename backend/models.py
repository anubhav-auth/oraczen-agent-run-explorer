from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
RunStatus = Literal["succeeded", "failed", "cancelled", "running"]
class TokenUsage(BaseModel):
    input: int = 0
    output: int = 0
class Step(BaseModel):
    index: int
    name: str
    tool: str
    status: str
    started_at: str
    duration_ms: int | float | None = None
    input: str = ""
    output: str | None = None
    tokens: TokenUsage = Field(default_factory=TokenUsage)
class RunSummary(BaseModel):
    id: str
    agent: str
    model: str
    status: str
    started_at: str
    ended_at: str | None = None
    duration_ms: int | float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    prompt: str = ""
    error: dict | None = None
    tenant_id: str = ""
class RunDetail(RunSummary):
    steps: list[Step] = Field(default_factory=list)
class RunsPage(BaseModel):
    items: list[RunSummary]
    total: int
    page: int
    page_size: int
