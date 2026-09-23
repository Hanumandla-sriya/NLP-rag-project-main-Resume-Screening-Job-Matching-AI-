import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..database.models import User, Resume
from ..schemas.resume import ResumeResponse, ResumeUploadResponse
from ..core.security import get_current_user
from ..core.config import settings
from ..services.resume_parser import ResumeParser
from ..services.nlp_engine import NLPEngine

router = APIRouter(prefix=f"{settings.API_V1_STR}/resumes", tags=["resumes"])

# Initialize services
resume_parser = ResumeParser()
nlp_engine = NLPEngine()


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a resume file"""
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Parse resume
    try:
        parsed_data = resume_parser.parse(file_path)
        raw_text = parsed_data['text']
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing resume: {str(e)}"
        )
    
    # Extract information using NLP
    try:
        extracted_info = nlp_engine.process_resume(raw_text)
    except Exception as e:
        # Continue even if NLP extraction fails
        extracted_info = {
            'skills': [],
            'experience': [],
            'education': []
        }
    
    # Create resume record
    resume = Resume(
        filename=file.filename,
        file_path=file_path,
        owner_id=current_user.id,
        raw_text=raw_text,
        skills=extracted_info.get('skills', []),
        experience=extracted_info.get('experience', []),
        education=extracted_info.get('education', [])
    )
    
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    return ResumeUploadResponse(
        id=resume.id,
        filename=resume.filename,
        message="Resume uploaded and processed successfully"
    )


@router.get("/", response_model=List[ResumeResponse])
def get_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all resumes for the current user"""
    resumes = db.query(Resume).filter(Resume.owner_id == current_user.id).all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific resume by ID"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.owner_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.owner_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete file if exists
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    
    db.delete(resume)
    db.commit()
    
    return None
