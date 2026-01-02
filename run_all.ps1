# PowerShell script to run backend and frontend at once in separate windows

# Path to backend and frontend
$backendPath = "backend"
$frontendPath = "frontend"

# Open backend in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendPath'; if (Test-Path .\venv) { .\venv\Scripts\Activate; }; python main.py"
)

# Open frontend in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendPath'; npm start"
) 