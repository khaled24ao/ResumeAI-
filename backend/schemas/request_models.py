"""Pydantic models for request body validation.

All API request payloads should be validated using these models.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, conint, constr

from backend.constants import (
    MAX_FILENAME_LENGTH,
    MAX_KEYWORDS,
    MAX_STRENGTHS,
    MAX_WEAKNESSES,
    MIN_KEYWORDS,
    MIN_STRENGTHS,
    MIN_WEAKNESSES,
    SCORE_MAX,
    SCORE_MIN,
    SUMMARY_MAX_LENGTH,
    SUMMARY_MIN_LENGTH,
)


class AnalysisResultRequest(BaseModel):
    """Request model for analysis result submission (used internally)."""

    score: conint(ge=SCORE_MIN, le=SCORE_MAX) = Field(
        ..., description="Resume score from 1-10"
    )
    strengths: list[constr(min_length=1)] = Field(
        ...,
        min_items=MIN_STRENGTHS,
        max_items=MAX_STRENGTHS,
        description="List of identified strengths",
    )
    weaknesses: list[constr(min_length=1)] = Field(
        ...,
        min_items=MIN_WEAKNESSES,
        max_items=MAX_WEAKNESSES,
        description="List of identified weaknesses",
    )
    improved_summary: constr(
        min_length=SUMMARY_MIN_LENGTH, max_length=SUMMARY_MAX_LENGTH
    ) = Field(..., description="Improved professional summary")
    keywords_missing: list[constr(min_length=1)] = Field(
        ...,
        min_items=MIN_KEYWORDS,
        max_items=MAX_KEYWORDS,
        description="List of missing important keywords",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "score": 8,
                "strengths": [
                    "Strong technical skills",
                    "Good experience",
                    "Clear structure",
                ],
                "weaknesses": ["Missing keywords", "Too long", "No summary"],
                "improved_summary": "Results-driven professional with extensive experience...",
                "keywords_missing": ["Python", "Docker", "AWS", "CI/CD", "Kubernetes"],
            }
        },
    )


class AnalysisMetadataRequest(BaseModel):
    """Metadata for analysis request."""

    filename: constr(max_length=MAX_FILENAME_LENGTH) = Field(
        ..., description="Original filename"
    )
    content_length: int | None = Field(None, ge=0, description="File size in bytes")
    content_type: str | None = Field(None, description="MIME type of uploaded file")

    model_config = ConfigDict(extra="forbid")


class HistoryQueryParams(BaseModel):
    """Query parameters for history endpoint."""

    page: conint(ge=1) = Field(1, description="Page number")
    per_page: conint(ge=1, le=100) = Field(20, description="Items per page (max 100)")
    sort_by: str | None = Field("created_at", description="Column to sort by")
    order: str | None = Field("desc", description="Sort order: 'asc' or 'desc'")

    model_config = ConfigDict(extra="forbid")


class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User email address")
    username: constr(min_length=3, max_length=50) = Field(..., description="Username")
    password: constr(min_length=8) = Field(
        ..., description="Password (min 8 characters)"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123",
            }
        },
    )


class UserLoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: constr(min_length=1) = Field(..., description="Password")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "securepassword123"}
        },
    )


class FeedbackRequest(BaseModel):
    """Request model for user feedback submission."""

    analysis_id: int | None = Field(None, description="Related analysis ID")
    rating: conint(ge=1, le=5) = Field(..., description="Rating 1-5")
    comment: constr(max_length=1000) | None = Field(
        None, description="Optional feedback comment"
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "analysis_id": 123,
                "rating": 5,
                "comment": "Very helpful analysis!",
            }
        },
    )
