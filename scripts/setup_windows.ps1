$ErrorActionPreference = "Stop"

Write-Host "Checking Python 3.13..."
$pythonCommand = $null
try {
    py -3.13 --version | Out-Null
    $pythonCommand = "py -3.13"
} catch {
    try {
        $versionOutput = python --version
        if ($versionOutput -match "Python 3\.13\.") {
            $pythonCommand = "python"
        }
    } catch {}
}

if ($null -eq $pythonCommand) {
    throw "Python 3.13 was not found. Install Python 3.13.x, close PowerShell, reopen it, then run this script again."
}

Write-Host "Creating virtual environment with $pythonCommand..."
if (Test-Path .venv) {
    Write-Host "Existing .venv found. Delete it manually if it was created using another Python version."
} else {
    Invoke-Expression "$pythonCommand -m venv .venv"
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Verifying virtual environment Python version..."
$venvVersion = python --version
Write-Host $venvVersion
if ($venvVersion -notmatch "Python 3\.13\.") {
    throw "The virtual environment is not using Python 3.13. Delete .venv and recreate it using: py -3.13 -m venv .venv"
}

Write-Host "Upgrading packaging tools..."
python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1

Write-Host "Installing project dependencies..."
pip install -r requirements.txt

Write-Host "Installing local project package in editable mode..."
pip install -e .

Write-Host "Copying .env.example to .env if missing..."
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
}

Write-Host "Running doctor check..."
python -m llm_sqa.cli doctor
