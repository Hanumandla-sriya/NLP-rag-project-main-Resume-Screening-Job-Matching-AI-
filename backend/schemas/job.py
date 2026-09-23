from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class JobBase(BaseModel):
    title: str
    description: str
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_level: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    resume_ids: Optional[List[int]] = None  # If None, match all resumes


class MatchScore(BaseModel):
    resume_id: int
    filename: str
    overall_score: float
    skill_match_score: Optional[float] = None
    experience_score: Optional[float] = None
    education_score: Optional[float] = None
    semantic_similarity: Optional[float] = None
    rank: int


class MatchResponse(BaseModel):
    job_id: int
    job_title: str
    matches: List[MatchScore]
    total_matched: int
