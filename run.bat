@echo off
chcp 65001 > nul
title Gemini 3.8 / 3.7 Flash Web Chatbot

echo ========================================================
echo   Google Gemini 3.8 / 3.7 Flash 웹 챗봇 서비스 시작
echo ========================================================
echo.

REM Check if python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [정보] 필수 패키지 확인 중...
pip install -r requirements.txt --quiet

REM Start browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

echo [정보] FastAPI 서버를 시작합니다 (http://localhost:8000)...
echo [종료] 서버를 중단하려면 Ctrl + C 를 누르세요.
echo.

python main.py
pause
