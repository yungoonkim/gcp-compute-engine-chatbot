@echo off
chcp 65001 > nul
cd /d "%~dp0compute_engine"
call run.bat
