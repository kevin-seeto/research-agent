@echo off
cd /d C:\Users\k_c_s\OneDrive\Desktop\research-agent
call venv\Scripts\activate.bat
python agent.py >> agent_log.txt 2>&1