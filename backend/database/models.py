from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="owner")
    jobs = relationship("Job", back_populates="owner")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Extracted information
    raw_text = Column(Text)
    skills = Column(JSON)  # List of skills
    experience = Column(JSON)  # List of experience entries
    education = Column(JSON)  # List of education entries
    
    # Embeddings
    embedding = Column(JSON)  # Vector embedding for semantic search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")
    matches = relationship("JobMatch", back_populates="resume")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON)  # List of required skills
    preferred_skills = Column(JSON)  # List of preferred skills
    experience_level = Column(String(50))  # e.g., "entry", "mid", "senior"
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Embeddings
    embedding = Column(JSON)  # Vector embedding for semantic search
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="jobs")
    matches = relationship("JobMatch", back_populates="job")


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    # Matching scores
    overall_score = Column(Float, nullable=False)  # Weighted overall score
    skill_match_score = Column(Float)  # Skill matching percentage
    experience_score = Column(Float)  # Experience relevance score
    education_score = Column(Float)  # Education alignment score
    semantic_similarity = Column(Float)  # Cosine similarity of embeddings
    
    # Ranking
    rank = Column(Integer)  # Rank position (1 = best match)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="matches")
    resume = relationship("Resume", back_populates="matches")
