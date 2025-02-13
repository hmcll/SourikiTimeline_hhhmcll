cd ./Python
powershell Expand-Archive -Force ./python-3.12.9-embed-amd64.zip ./Runtime
copy "requirements.txt" "./Runtime/"
copy "get-pip.py" "./Runtime/"
cd ./Runtime
"./python.exe" get-pip.py
ECHO Lib/site-packages >> python312._pth
"./Scripts/pip.exe" install --upgrade -r requirements.txt
cd ..
powershell Expand-Archive -Force ./imgui_bundle.zip ./Runtime/Lib/site-packages

pause