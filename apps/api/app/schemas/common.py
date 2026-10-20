from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorOut(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    hint: Optional[str] = Field(None, description="Actionable suggestion or hint to resolve the error")
    request_id: Optional[str] = Field(None, description="Unique correlation id for the request")


class SourceRef(BaseModel):
    source_type: str = Field(..., description="Type of source: transcript, frame, document, etc.")
    chunk_id: Optional[str] = Field(None, description="Unique chunk identifier")
    timestamp_s: Optional[float] = Field(None, description="Video timestamp in seconds")
    timestamp_formatted: Optional[str] = Field(None, description="Formatted timestamp mm:ss")
    page_number: Optional[int] = Field(None, description="Page number for document sources")
    slide_number: Optional[int] = Field(None, description="Slide number for presentation sources")
    label: Optional[str] = Field(None, description="Display label or title for the source reference")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional source metadata")


class Citation(BaseModel):
    chunk_id: str = Field(..., description="Referenced chunk identifier")
    text: Optional[str] = Field(None, description="Referenced snippet text or transcription")
    source_ref: Optional[SourceRef] = Field(None, description="Server-resolved source coordinates")
