@echo off

echo Starting backend...
start cmd /k python Y:\ai-chat\Phone\phone_test.py

timeout /t 2 >nul

echo Starting frontend...
cd /d Y:\ai-chat\Phone\phone_tester
start cmd /k npm run dev

timeout /t 3 >nul

start http://localhost:5173