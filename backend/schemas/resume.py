from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ResumeBase(BaseModel):
    filename: str


class ResumeCreate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: int
    owner_id: int
    raw_text: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[Dict[str, Any]]] = None
    education: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    id: int
    filename: str
    message: str
