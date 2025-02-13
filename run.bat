setlocal
SET PYTHONPATH=%~dp0;%PYTHONPATH%
"./Python/Runtime/python.exe" ./scripts/launch.py
endlocal 
