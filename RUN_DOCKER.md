# How to Run docker-compose.yml

## Quick Start

### Option 1: Using Docker Compose V2 (Recommended)

**On Windows (PowerShell):**
```powershell
# Navigate to project directory
cd C:\Users\mohds\rag_project

# Create .env file (if not exists)
if (!(Test-Path .env)) { Copy-Item env.example .env }

# Run docker compose (note: space, not hyphen)
docker compose up --build
```

**On WSL/Ubuntu:**
```bash
# Navigate to project directory
cd ~/rag_project

# Create .env file (if not exists)
cp env.example .env

# Fix Docker environment issue (if you got the http+docker error)
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Run docker compose (note: space, not hyphen)
docker compose up --build
```

### Option 2: Using Legacy docker-compose V1

**On Windows (PowerShell):**
```powershell
cd C:\Users\mohds\rag_project
if (!(Test-Path .env)) { Copy-Item env.example .env }
docker-compose up --build
```

**On WSL/Ubuntu (if you must use v1):**
```bash
cd ~/rag_project
cp env.example .env

# CRITICAL: Unset problematic Docker environment variables
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Then run
docker-compose up --build
```

## Step-by-Step Instructions

### Step 1: Prerequisites Check

**Check Docker is running:**
```bash
# Windows PowerShell
docker version

# WSL/Ubuntu
docker version
```

**Check Docker Compose version:**
```bash
# Docker Compose V2 (recommended)
docker compose version

# OR Legacy V1
docker-compose --version
```

### Step 2: Create Environment File

Create a `.env` file in the project root:

**Windows PowerShell:**
```powershell
Copy-Item env.example .env
```

**WSL/Ubuntu:**
```bash
cp env.example .env
```

**Or manually create `.env` with:**
```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=resume_screening
SECRET_KEY=your-secret-key-change-in-production-use-a-long-random-string
```

### Step 3: Create Uploads Directory

**Windows PowerShell:**
```powershell
New-Item -ItemType Directory -Force -Path uploads
```

**WSL/Ubuntu:**
```bash
mkdir -p uploads
```

### Step 4: Run Docker Compose

**Build and start all services:**
```bash
docker compose up --build
```

**Or run in detached mode (background):**
```bash
docker compose up --build -d
```

**View logs:**
```bash
docker compose logs -f
```

**Stop services:**
```bash
docker compose down
```

**Stop and remove volumes (clean slate):**
```bash
docker compose down -v
```

## Troubleshooting

### Error: "Not supported URL scheme http+docker"

**Solution:** Unset Docker environment variables in WSL:
```bash
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
```

Or add to your `~/.bashrc` or `~/.zshrc`:
```bash
export DOCKER_HOST=unix:///var/run/docker.sock
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH
```

### Error: "Cannot connect to Docker daemon"

**Solution:** Make sure Docker Desktop is running (Windows) or Docker service is running (Linux):
```bash
# Windows: Start Docker Desktop application

# Linux/WSL: Check Docker service
sudo service docker start
# OR
sudo systemctl start docker
```

### Error: "Port already in use"

**Solution:** Either stop the conflicting service or change ports in `docker-compose.yml`:
- Port 5432 (PostgreSQL) - change line 12
- Port 8000 (Backend) - change line 27
- Port 3000 (Frontend) - change line 47

### Error: "Build failed" or "Module not found"

**Solution:** Make sure you're in the project root directory:
```bash
cd C:\Users\mohds\rag_project  # Windows
cd ~/rag_project                # WSL
```

### Frontend can't connect to backend

**Check:** Make sure `REACT_APP_API_URL` in `.env` matches your backend URL:
```env
REACT_APP_API_URL=http://localhost:8000
```

## Accessing the Application

Once running successfully:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (username: postgres, password: postgres)

## Useful Commands

**View running containers:**
```bash
docker compose ps
```

**View logs for specific service:**
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs db
```

**Rebuild specific service:**
```bash
docker compose up --build backend
```

**Execute command in running container:**
```bash
docker compose exec backend bash
docker compose exec db psql -U postgres -d resume_screening
```

**Clean up everything:**
```bash
docker compose down -v --remove-orphans
docker system prune -a
```

## Production Deployment

For production, update `.env` with:
- Strong `SECRET_KEY`
- Production database credentials
- Proper CORS origins in `backend/main.py`
- SSL/TLS certificates
- Reverse proxy (Nginx)
