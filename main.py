
allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .database.session import init_db
from .api import auth, resumes, jobs


# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Resume Screening & Job Matching API",
    description="NLP-powered resume screening and job matching system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Resume Screening & Job Matching API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

File Name to Write: backend/main.py

