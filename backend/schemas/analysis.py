from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class AnalysisRequest(BaseModel):
    """Validation model for analysis request metadata."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_length: Optional[int] = Field(None, ge=0, le=5*1024*1024)  # Max 5MB
    content_type: Optional[str] = Field(None, pattern=r"^application/pdf$")

    model_config = ConfigDict(extra="forbid")

class AnalysisResult(BaseModel):
    """Structured analysis result from AI."""
    score: int = Field(..., ge=1, le=10)
    strengths: List[str] = Field(..., min_length=1, max_length=10)
    weaknesses: List[str] = Field(..., min_length=1, max_length=10)
    improved_summary: str = Field(..., min_length=10, max_length=2000)
    keywords_missing: List[str] = Field(..., min_length=1, max_length=20)

    model_config = ConfigDict(extra="forbid")

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    details: Optional[str] = None
