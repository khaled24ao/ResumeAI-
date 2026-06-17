"""Analysis schemas with Pydantic validation."""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, validator

class AnalysisRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=50 * 1024 * 1024)
    language: str = Field(default='en')

    @validator('filename')
    def validate_filename(cls, v):
        if '../' in v or '..\\' in v:
            raise ValueError('Invalid filename')
        return v

class AnalysisResponse(BaseModel):
    success: bool
    analysis_id: str
    score: int = Field(..., ge=0, le=100)
    strengths: List[str]
    weaknesses: List[str]
    summary: str
