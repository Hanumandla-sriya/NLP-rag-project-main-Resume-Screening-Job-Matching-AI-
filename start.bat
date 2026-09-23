@echo off
REM Resume Screening AI - Startup Script for Windows

echo Starting Resume Screening AI...

REM Check if .env exists
if not exist .env (
    echo Creating .env file from env.example...
    copy env.example .env
    echo Please edit .env file with your configuration
)

REM Create uploads directory
if not exist uploads mkdir uploads

REM Start Docker Compose
echo Starting Docker containers...
docker compose up --build
