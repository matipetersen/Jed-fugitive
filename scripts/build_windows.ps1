<#
Windows build script for PowerShell. Run on a Windows runner (or locally in PowerShell).
Creates a venv, installs pyinstaller and requirements, and builds a single-file exe.
#>
param(
    [string]$Python = "python"
)

Set-StrictMode -Version Latest
$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $root

Write-Host "Creating virtualenv..."
& $Python -m venv .venv_build
& .\.venv_build\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r ..\requirements-build.txt
pip install -r ..\requirements.txt

Write-Host "Running pyinstaller..."
pyinstaller --noconfirm --onefile --name "jedi-fugitive" ..\src\jedi_fugitive\main.py

Write-Host "Build finished. Dist artifact is in dist\jedi-fugitive.exe"
Pop-Location
