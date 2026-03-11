from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ListingInput(BaseModel):
    title: str = Field(min_length=4, max_length=512)
    description: str = Field(min_length=8, max_length=5000)
    brand: str = Field(min_length=2, max_length=128)
    category: str = Field(min_length=2, max_length=128)
    price: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)
    seller_age_days: int | None = Field(default=None, ge=0)
    seller_rating: float | None = Field(default=None, ge=1.0, le=5.0)
    seller_sales_count: int | None = Field(default=None, ge=0)
    review_count: int | None = Field(default=None, ge=0)
    shipping_country: str | None = Field(default=None, max_length=64)
    return_policy_days: int | None = Field(default=None, ge=0, le=365)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return value.upper()


class ModelMeta(BaseModel):
    version: str
    training_timestamp: str


class Highlight(BaseModel):
    phrase: str
    start: int
    end: int


class ExplanationItem(BaseModel):
    source: Literal["structured", "text", "fusion"]
    feature: str
    contribution: float
    detail: str


class AnalysisResponse(BaseModel):
    analysis_id: int
    listing_id: int
    risk_score: float
    action: Literal["APPROVE", "REVIEW", "BLOCK"]
    structured_prob: float
    text_prob: float
    fused_prob: float
    llm_summary: str | None = None
    llm_provider: str | None = None
    explanations: list[ExplanationItem]
    highlights: list[Highlight]
    model: ModelMeta


class ListingResponse(ListingInput):
    id: int
    created_at: datetime


class ListingWithAnalysis(BaseModel):
    listing: ListingResponse
    latest_analysis: AnalysisResponse | None = None


class FeedbackRequest(BaseModel):
    analysis_id: int
    label: Literal["counterfeit", "legit", "unsure"]
    notes: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    analysis_id: int
    label: str
    notes: str | None
    created_at: datetime


class MetricsResponse(BaseModel):
    model_validation: dict
    live_marketplace: dict


class ModelInfoResponse(BaseModel):
    version: str
    trained_at: str
    thresholds: dict
    artifacts: dict
