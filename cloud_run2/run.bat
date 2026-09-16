@echo off
chcp 65001 > nul
title Gemini Web Chatbot (Cloud Run - ADC Mode)
cd /d "%~dp0"

echo ========================================================
echo   Google Gemini 웹 챗봇 로컬 테스트 (ADC 인증 모드)
echo ========================================================
echo.

REM Check if python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다.
    pause
    exit /b 1
)

REM Check ADC credentials
echo [1/3] Application Default Credentials (ADC) 상태 확인 중...
gcloud auth application-default print-access-token >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [알림] ADC 자격증명이 필요합니다. 아래 명령어로 먼저 로그인해 주세요:
    echo        gcloud auth application-default login
    echo.
)

REM Install dependencies if needed
echo [2/3] 필수 패키지 확인 중...
pip install -r requirements.txt --quiet

REM Start browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080"

echo [3/3] FastAPI 서버를 시작합니다 (http://localhost:8080)...
echo [종료] 서버를 중단하려면 Ctrl + C 를 누르세요.
echo.

set PORT=8080
python main.py
pause
