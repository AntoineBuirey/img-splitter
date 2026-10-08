$ErrorActionPreference = "Stop"

uv run pyinstaller --noconfirm --clean img_splitter.spec

Write-Host "Executable created at: $((Resolve-Path 'dist\img-splitter.exe').Path)"
