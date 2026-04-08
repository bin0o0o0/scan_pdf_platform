$ErrorActionPreference = "Stop"

# The machine currently has a system proxy configured in Internet Settings.
# When that proxy process is not running, pip still tries to use it and fails.
# We only bypass the proxy inside this script process so we do not mutate the
# user's global network configuration.
$env:NO_PROXY = "*"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""

$python = Join-Path $PSScriptRoot "..\\.venv\\Scripts\\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating Python 3.11 virtual environment..."
    py -3.11 -m venv (Join-Path $PSScriptRoot "..\\.venv")
}

Write-Host "Upgrading pip..."
& $python -m pip install --upgrade pip `
    -i https://pypi.tuna.tsinghua.edu.cn/simple `
    --trusted-host pypi.tuna.tsinghua.edu.cn

Write-Host "Installing backend requirements..."
& $python -m pip install -r (Join-Path $PSScriptRoot "..\\backend\\requirements.txt") `
    -i https://pypi.tuna.tsinghua.edu.cn/simple `
    --trusted-host pypi.tuna.tsinghua.edu.cn

Write-Host "Backend dependencies are ready."
