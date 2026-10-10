param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$studio = $PSScriptRoot
$repo = Split-Path -Parent $studio

Push-Location $repo
try {
    if (-not $SkipTests) {
        $env:QT_QPA_PLATFORM = "offscreen"
        python -m pytest -q .\tests
        if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
    }

    python -m PyInstaller --noconfirm --clean (Join-Path $studio "LongY_Studio.spec")

    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    $dist = Join-Path $repo "dist\LongY_Studio"
    if (-not (Test-Path $dist)) { throw "Build output not found: $dist" }
    Write-Host "Built $dist"
}
finally {
    Pop-Location
}
