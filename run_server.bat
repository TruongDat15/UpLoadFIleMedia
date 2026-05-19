er@echo off
REM Simple script to run FastAPI server with uvicorn
REM Run this from project root: run_server.bat

echo 🚀 Starting FastAPI Server...
echo.

REM Option 1: With reload (development)
cd Server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

REM Option 2: Without reload (production)
REM uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

echo.
echo 🛑 Server stopped

