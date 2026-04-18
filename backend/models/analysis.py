"""Analysis-related database models."""

import json

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.models import Base


class Analysis(Base):
    """Stores analysis results for each resume processed."""

    __tablename__ = "analyses"

    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=True)  # in bytes

    # Analysis results
    score = Column(Integer, nullable=False, index=True)
    strengths = Column(Text, nullable=False)  # JSON array
    weaknesses = Column(Text, nullable=False)  # JSON array
    improved_summary = Column(Text, nullable=False)
    keywords_missing = Column(Text, nullable=False)  # JSON array

    # Metadata
    processing_time_ms = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(255), nullable=True)

    # Relationships
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # user = relationship("User", back_populates="analyses")

    def __repr__(self) -> str:
        return (
            f"<Analysis(id={self.id}, filename='{self.filename}', score={self.score})>"
        )

    @property
    def strengths_list(self) -> list:
        """Get strengths as Python list."""
        return json.loads(self.strengths) if self.strengths else []

    @property
    def weaknesses_list(self) -> list:
        """Get weaknesses as Python list."""
        return json.loads(self.weaknesses) if self.weaknesses else []

    @property
    def keywords_missing_list(self) -> list:
        """Get missing keywords as Python list."""
        return json.loads(self.keywords_missing) if self.keywords_missing else []

    @classmethod
    def from_analysis_result(cls, filename: str, result: dict, **kwargs):
        """
        Create Analysis instance from validated analysis result.

        Args:
            filename: Original filename
            result: AnalysisResult dictionary
            **kwargs: Additional metadata

        Returns:
            Analysis instance (not yet committed to DB)
        """
        return cls(
            filename=filename,
            strengths=json.dumps(result["strengths"]),
            weaknesses=json.dumps(result["weaknesses"]),
            improved_summary=result["improved_summary"],
            keywords_missing=json.dumps(result["keywords_missing"]),
            score=result["score"],
            **kwargs,
        )

    @property
    def strengths_list(self) -> list:
        """Get strengths as Python list."""
        return json.loads(self.strengths) if self.strengths else []

    @property
    def weaknesses_list(self) -> list:
        """Get weaknesses as Python list."""
        return json.loads(self.weaknesses) if self.weaknesses else []

    @property
    def keywords_missing_list(self) -> list:
        """Get missing keywords as Python list."""
        return json.loads(self.keywords_missing) if self.keywords_missing else []

    @classmethod
    def from_analysis_result(cls, filename: str, result: dict, **kwargs):
        """
        Create Analysis instance from validated analysis result.

        Args:
            filename: Original filename
            result: AnalysisResult dictionary
            **kwargs: Additional metadata

        Returns:
            Analysis instance (not yet committed to DB)
        """
        return cls(
            filename=filename,
            strengths=json.dumps(result["strengths"]),
            weaknesses=json.dumps(result["weaknesses"]),
            improved_summary=result["improved_summary"],
            keywords_missing=json.dumps(result["keywords_missing"]),
            score=result["score"],
            **kwargs,
        )
