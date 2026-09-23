from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..database.models import User, Job, Resume, JobMatch
from ..schemas.job import JobCreate, JobResponse, MatchRequest, MatchResponse, MatchScore
from ..core.security import get_current_user
from ..core.config import settings
from ..services.matching_service import MatchingService

router = APIRouter(prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])

# Initialize matching service
matching_service = MatchingService()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    
    # Generate embedding for job description
    job_embedding = matching_service.generate_embedding(job_data.description)
    
    job = Job(
        title=job_data.title,
        description=job_data.description,
        required_skills=job_data.required_skills or [],
        preferred_skills=job_data.preferred_skills or [],
        experience_level=job_data.experience_level,
        owner_id=current_user.id,
        embedding=job_embedding
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all jobs for the current user"""
    jobs = db.query(Job).filter(Job.owner_id == current_user.id).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job by ID"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.owner_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/{job_id}/match", response_model=MatchResponse)
def match_candidates(
    job_id: int,
    match_request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match candidates with a job posting"""
    
    # Get job
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.owner_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get resumes to match
    if match_request.resume_ids:
        resumes = db.query(Resume).filter(
            Resume.id.in_(match_request.resume_ids),
            Resume.owner_id == current_user.id
        ).all()
    else:
        # Match all resumes
        resumes = db.query(Resume).filter(Resume.owner_id == current_user.id).all()
    
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resumes found to match"
        )
    
    # Get or generate job embedding
    if not job.embedding:
        job.embedding = matching_service.generate_embedding(job.description)
        db.commit()
    
    matches = []
    
    # Match each resume
    for resume in resumes:
        # Generate resume embedding if not exists
        if not resume.embedding:
            resume.embedding = matching_service.generate_embedding(resume.raw_text or "")
            db.commit()
        
        # Calculate matching scores
        match_result = matching_service.match_resume_to_job(
            resume_text=resume.raw_text or "",
            resume_skills=resume.skills or [],
            resume_experience=resume.experience or [],
            resume_education=resume.education or [],
            job_description=job.description,
            job_skills=job.required_skills or [],
            job_experience_level=job.experience_level
        )
        
        # Update resume embedding if generated
        if not resume.embedding:
            resume.embedding = match_result['resume_embedding']
            db.commit()
        
        # Create or update job match record
        existing_match = db.query(JobMatch).filter(
            JobMatch.job_id == job_id,
            JobMatch.resume_id == resume.id
        ).first()
        
        if existing_match:
            match_record = existing_match
        else:
            match_record = JobMatch(
                job_id=job_id,
                resume_id=resume.id
            )
            db.add(match_record)
        
        match_record.overall_score = match_result['overall_score']
        match_record.skill_match_score = match_result['skill_match_score']
        match_record.experience_score = match_result['experience_score']
        match_record.education_score = match_result['education_score']
        match_record.semantic_similarity = match_result['semantic_similarity']
        
        matches.append({
            'resume_id': resume.id,
            'filename': resume.filename,
            'overall_score': match_result['overall_score'],
            'skill_match_score': match_result['skill_match_score'],
            'experience_score': match_result['experience_score'],
            'education_score': match_result['education_score'],
            'semantic_similarity': match_result['semantic_similarity']
        })
    
    db.commit()
    
    # Sort matches by overall score (descending)
    matches.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Assign ranks
    for rank, match_data in enumerate(matches, start=1):
        match_data['rank'] = rank
        
        # Update rank in database
        match_record = db.query(JobMatch).filter(
            JobMatch.job_id == job_id,
            JobMatch.resume_id == match_data['resume_id']
        ).first()
        if match_record:
            match_record.rank = rank
    
    db.commit()
    
    return MatchResponse(
        job_id=job_id,
        job_title=job.title,
        matches=[MatchScore(**m) for m in matches],
        total_matched=len(matches)
    )


@router.get("/{job_id}/rankings", response_model=MatchResponse)
def get_rankings(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ranked candidates for a job"""
    
    # Get job
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.owner_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get all matches for this job
    job_matches = db.query(JobMatch).filter(
        JobMatch.job_id == job_id
    ).order_by(JobMatch.rank.asc()).all()
    
    matches = []
    for match in job_matches:
        resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
        if resume:
            matches.append(MatchScore(
                resume_id=resume.id,
                filename=resume.filename,
                overall_score=match.overall_score,
                skill_match_score=match.skill_match_score,
                experience_score=match.experience_score,
                education_score=match.education_score,
                semantic_similarity=match.semantic_similarity,
                rank=match.rank or 0
            ))
    
    return MatchResponse(
        job_id=job_id,
        job_title=job.title,
        matches=matches,
        total_matched=len(matches)
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job posting"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.owner_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Delete associated matches
    db.query(JobMatch).filter(JobMatch.job_id == job_id).delete()
    
    db.delete(job)
    db.commit()
    
    return None
