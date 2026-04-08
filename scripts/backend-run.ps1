$ErrorActionPreference = "Stop"

# Clear proxy-related variables in the current shell so follow-up commands
# like pip or pytest in the same session do not inherit the broken proxy.
$env:NO_PROXY = "*"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""

# The checked-in .env is designed for Docker Compose, where MySQL is reachable
# by the service name "mysql". When running Flask directly on Windows, that
# hostname does not resolve, so we point the local process at the published port.
$env:MYSQL_HOST = "127.0.0.1"
$env:MYSQL_PORT = "3306"

$python = Join-Path $PSScriptRoot "..\\.venv\\Scripts\\python.exe"

if (-not (Test-Path $python)) {
    throw "No .venv found. Run scripts\\backend-bootstrap.ps1 first."
}

Push-Location (Join-Path $PSScriptRoot "..\\backend")
try {
    & $python run.py
}
finally {
    Pop-Location
}
