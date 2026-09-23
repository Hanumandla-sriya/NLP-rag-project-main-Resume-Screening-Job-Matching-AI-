# Setup Instructions

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local development)
- Node.js 16+ (for local frontend development)

## Quick Start with Docker

1. **Clone the repository** (if applicable)

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   Edit `.env` and update the values as needed.

3. **Start all services**:
   ```bash
   docker compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Local Development Setup

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set up database**:
   - Make sure PostgreSQL is running
   - Update `DATABASE_URL` in `.env` file
   - The database tables will be created automatically on first run

6. **Run the server**:
   ```bash
   cd ..
   uvicorn backend.main:app --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

   The frontend will be available at http://localhost:3000

## First Time Setup

1. **Register a user account**:
   - Go to http://localhost:3000/register
   - Create an account

2. **Upload a resume**:
   - After logging in, go to the "Resumes" tab
   - Upload a PDF or DOCX resume file

3. **Create a job posting**:
   - Go to the "Jobs" tab
   - Fill in job details and create a posting

4. **Match candidates**:
   - Click "Match Candidates" on a job posting
   - View the ranked results in the "Match Results" tab

## Troubleshooting

### Backend Issues

- **Database connection error**: Make sure PostgreSQL is running and DATABASE_URL is correct
- **spaCy model not found**: Run `python -m spacy download en_core_web_sm`
- **Port already in use**: Change the port in `docker-compose.yml` or stop the conflicting service

### Frontend Issues

- **API connection error**: Make sure backend is running and REACT_APP_API_URL is set correctly
- **npm install fails**: Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

### Docker Issues

- **Build fails**: Make sure Docker has enough resources allocated (at least 4GB RAM)
- **Container won't start**: Check logs with `docker-compose logs`
- **Port conflicts**: Update ports in `docker-compose.yml`

## Environment Variables

Key environment variables (see `.env.example`):
Key environment variables (see `env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT tokens (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token expiration time
- `REACT_APP_API_URL`: Backend API URL for frontend

## Production Deployment

For production deployment:

1. Update `SECRET_KEY` with a strong random string
2. Set `DATABASE_URL` to your production database
3. Configure proper CORS origins in `backend/main.py`
4. Use environment-specific Docker Compose files
5. Set up SSL/TLS certificates
6. Configure reverse proxy (Nginx)
7. Set up monitoring and logging
