@echo off
call .\venv\Scripts\activate
start cmd /k python fast_api.py
cd "./react_app"
start cmd /k npm start