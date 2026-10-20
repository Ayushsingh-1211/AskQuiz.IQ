from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None


class VideoOut(BaseModel):
    id: str
    user_id: str
    title: str
    url: Optional[str] = None
    file_path: Optional[str] = None
    duration_s: Optional[float] = None
    status: str
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    visual_unavailable: bool = False
    stream_url: Optional[str] = None
    is_ready_text: bool = False
    is_ready_full: bool = False


class VideoListOut(BaseModel):
    items: List[VideoOut]
    total: int
