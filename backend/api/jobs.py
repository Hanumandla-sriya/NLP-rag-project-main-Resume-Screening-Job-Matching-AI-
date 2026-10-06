"""
Job management and resume-to-job matching API routes.
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.security import get_current_user
from ..database.models import Job, JobMatch, Resume, User
from ..database.session import get_db
from ..schemas.job import (
    JobCreate,
    JobResponse,
    MatchRequest,
    MatchResponse,
    MatchScore,
)
from ..services.matching_service import MatchingService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix=f"{settings.API_V1_STR}/jobs",
    tags=["jobs"],
)


# Load the semantic matching model once when the application starts.
matching_service = MatchingService()


def _has_embedding(value: Any) -> bool:
    """Safely check whether a stored embedding exists and is non-empty."""
    if value is None:
        return False

    try:
        return len(value) > 0
    except TypeError:
        return False


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    """
    Create a new job posting and generate its semantic embedding.
    """
    try:
        description = job_data.description.strip()

        if not description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description cannot be empty.",
            )

        job_embedding = matching_service.generate_embedding(
            description
        )

        job = Job(
            title=job_data.title.strip(),
            description=description,
            required_skills=job_data.required_skills or [],
            preferred_skills=job_data.preferred_skills or [],
            experience_level=job_data.experience_level,
            owner_id=current_user.id,
            embedding=job_embedding,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(
            "Job created successfully. job_id=%s user_id=%s",
            job.id,
            current_user.id,
        )

        return job

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error while creating job."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job.",
        ) from exc

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Unexpected error while creating job."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job.",
        ) from exc


@router.get(
    "/",
    response_model=List[JobResponse],
)
def get_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Job]:
    """
    Return all jobs belonging to the authenticated user.
    """
    return (
        db.query(Job)
        .filter(Job.owner_id == current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    """
    Return a specific job belonging to the authenticated user.
    """
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.owner_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return job


@router.post(
    "/{job_id}/match",
    response_model=MatchResponse,
)
def match_candidates(
    job_id: int,
    match_request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchResponse:
    """
    Match resumes against a job and return candidates ranked
    by their overall compatibility score.
    """

    # ---------------------------------------------------------
    # 1. Retrieve and authorize the job.
    # ---------------------------------------------------------
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.owner_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    try:
        # -----------------------------------------------------
        # 2. Ensure the job has an embedding.
        # -----------------------------------------------------
        if not _has_embedding(job.embedding):
            job.embedding = matching_service.generate_embedding(
                job.description
            )

        # -----------------------------------------------------
        # 3. Retrieve resumes to match.
        # -----------------------------------------------------
        if match_request.resume_ids:
            resumes = (
                db.query(Resume)
                .filter(
                    Resume.id.in_(match_request.resume_ids),
                    Resume.owner_id == current_user.id,
                )
                .all()
            )
        else:
            resumes = (
                db.query(Resume)
                .filter(
                    Resume.owner_id == current_user.id
                )
                .all()
            )

        if not resumes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resumes found to match.",
            )

        matches = []

        # -----------------------------------------------------
        # 4. Match each resume against the job.
        # -----------------------------------------------------
        for resume in resumes:

            # Generate the resume embedding only if it does
            # not already exist.
            if not _has_embedding(resume.embedding):
                resume.embedding = (
                    matching_service.generate_embedding(
                        resume.raw_text or ""
                    )
                )

            match_result = (
                matching_service.match_resume_to_job(
                    resume_text=resume.raw_text or "",
                    resume_skills=resume.skills or [],
                    resume_experience=resume.experience or [],
                    resume_education=resume.education or [],
                    job_description=job.description,
                    job_skills=job.required_skills or [],
                    job_experience_level=job.experience_level,
                    resume_embedding=resume.embedding,
                    job_embedding=job.embedding,
                )
            )

            # -------------------------------------------------
            # 5. Create or update JobMatch.
            # -------------------------------------------------
            match_record = (
                db.query(JobMatch)
                .filter(
                    JobMatch.job_id == job.id,
                    JobMatch.resume_id == resume.id,
                )
                .first()
            )

            if match_record is None:
                match_record = JobMatch(
                    job_id=job.id,
                    resume_id=resume.id,
                )
                db.add(match_record)

            match_record.overall_score = (
                match_result["overall_score"]
            )
            match_record.skill_match_score = (
                match_result["skill_match_score"]
            )
            match_record.experience_score = (
                match_result["experience_score"]
            )
            match_record.education_score = (
                match_result["education_score"]
            )
            match_record.semantic_similarity = (
                match_result["semantic_similarity"]
            )

            matches.append(
                {
                    "record": match_record,
                    "resume_id": resume.id,
                    "filename": resume.filename,
                    "overall_score": match_result[
                        "overall_score"
                    ],
                    "skill_match_score": match_result[
                        "skill_match_score"
                    ],
                    "experience_score": match_result[
                        "experience_score"
                    ],
                    "education_score": match_result[
                        "education_score"
                    ],
                    "semantic_similarity": match_result[
                        "semantic_similarity"
                    ],
                    "matched_skills": match_result[
                        "matched_skills"
                    ],
                    "missing_skills": match_result[
                        "missing_skills"
                    ],
                }
            )

        # -----------------------------------------------------
        # 6. Rank candidates.
        # -----------------------------------------------------
        matches.sort(
            key=lambda item: item["overall_score"],
            reverse=True,
        )

        for rank, match_data in enumerate(
            matches,
            start=1,
        ):
            match_data["rank"] = rank
            match_data["record"].rank = rank

        # -----------------------------------------------------
        # 7. Commit everything as one transaction.
        # -----------------------------------------------------
        db.commit()

        logger.info(
            "Resume matching completed. job_id=%s "
            "user_id=%s candidates=%s",
            job.id,
            current_user.id,
            len(matches),
        )

        return MatchResponse(
            job_id=job.id,
            job_title=job.title,
            matches=[
                MatchScore(
                    resume_id=item["resume_id"],
                    filename=item["filename"],
                    overall_score=item["overall_score"],
                    skill_match_score=item[
                        "skill_match_score"
                    ],
                    experience_score=item[
                        "experience_score"
                    ],
                    education_score=item[
                        "education_score"
                    ],
                    semantic_similarity=item[
                        "semantic_similarity"
                    ],
                    matched_skills=item[
                        "matched_skills"
                    ],
                    missing_skills=item[
                        "missing_skills"
                    ],
                    rank=item["rank"],
                )
                for item in matches
            ],
            total_matched=len(matches),
        )

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error while matching resumes. "
            "job_id=%s",
            job_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to match resumes.",
        ) from exc

    except Exception as exc:
        db.rollback()

        logger.exception(
            "Unexpected error while matching resumes. "
            "job_id=%s",
            job_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process resume matching.",
        ) from exc


@router.get(
    "/{job_id}/rankings",
    response_model=MatchResponse,
)
def get_rankings(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchResponse:
    """
    Return previously calculated candidate rankings for a job.
    """

    # Verify ownership of the job.
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.owner_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    # Retrieve matches and associated resumes using a join.
    results = (
        db.query(JobMatch, Resume)
        .join(
            Resume,
            Resume.id == JobMatch.resume_id,
        )
        .filter(
            JobMatch.job_id == job_id,
            Resume.owner_id == current_user.id,
        )
        .order_by(
            JobMatch.rank.asc(),
            JobMatch.overall_score.desc(),
        )
        .all()
    )

    matches = []

    for match, resume in results:
        # Pass resume_text so matched/missing skills here are
        # identical to what the match endpoint returns.
        skill_details = (
            matching_service.get_skill_match_details(
                resume_skills=resume.skills or [],
                job_skills=job.required_skills or [],
                resume_text=resume.raw_text or "",
            )
        )

        matches.append(
            MatchScore(
                resume_id=match.resume_id,
                filename=resume.filename,
                overall_score=match.overall_score,
                skill_match_score=match.skill_match_score,
                experience_score=match.experience_score,
                education_score=match.education_score,
                semantic_similarity=match.semantic_similarity,
                matched_skills=skill_details[
                    "matched_skills"
                ],
                missing_skills=skill_details[
                    "missing_skills"
                ],
                rank=match.rank or 0,
            )
        )

    return MatchResponse(
        job_id=job.id,
        job_title=job.title,
        matches=matches,
        total_matched=len(matches),
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a job and all associated match records.
    """

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.owner_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    try:
        # Delete associated match records first.
        (
            db.query(JobMatch)
            .filter(JobMatch.job_id == job_id)
            .delete(
                synchronize_session=False
            )
        )

        db.delete(job)
        db.commit()

        logger.info(
            "Job deleted successfully. job_id=%s user_id=%s",
            job_id,
            current_user.id,
        )

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error while deleting job. "
            "job_id=%s",
            job_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job.",
        ) from exc