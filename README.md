# Resume Screening & Job Matching AI

A scalable NLP-powered system for parsing resumes, extracting candidate information, and matching them with job descriptions using advanced ML techniques.

## Features

- 📄 **Resume Parsing**: Supports PDF and DOCX formats
- 🔍 **Information Extraction**: Automatically extracts skills, experience, and education
- 🎯 **Smart Matching**: Uses BERT embeddings and semantic similarity for candidate-job matching
- 📊 **Ranking System**: Automatically ranks candidates based on multiple factors
- 🔐 **Authentication**: Secure JWT-based authentication
- 🚀 **Scalable Architecture**: Docker-based deployment with PostgreSQL

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **NLP/ML**: spaCy, Sentence Transformers (BERT), scikit-learn
- **Frontend**: React, TypeScript
- **Deployment**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Node.js 16+ (for local frontend development)

### Using Docker (Recommended)

1. Clone the repository
2. Copy `env.example` to `.env` and configure:
   ```bash
   cp env.example .env
   ```

3. Start all services:
   ```bash
   docker compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start server
cd ..
uvicorn backend.main:app --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Project Structure

```
resume_screening/
├── backend/
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core configuration and security
│   ├── database/         # Database models and session
│   ├── services/         # Business logic services
│   ├── schemas/          # Pydantic schemas
│   └── main.py           # FastAPI application entry
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API service calls
│   │   └── App.js        # Main app component
│   └── package.json
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/resumes/upload` - Upload resume
- `GET /api/v1/resumes/{id}` - Get resume details
- `POST /api/v1/jobs` - Create job posting
- `POST /api/v1/jobs/{job_id}/match` - Match candidates with job
- `GET /api/v1/jobs/{job_id}/rankings` - Get ranked candidates

## License

MIT
