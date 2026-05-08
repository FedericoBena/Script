# Attiva il venv
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$venvPath = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
} else {
    Write-Host "⚠️  Venv non trovato. Esegui: python settings/setup.py" -ForegroundColor Yellow
}

# Blocca pip install diretto
function pip {
    $cmd = $args[0]
    if ($cmd -eq "install") {
        $pkgs = $args[1..($args.Length-1)] -join " "
        Write-Host ""
        Write-Host "🚫 'pip install' diretto non aggiorna requirements.txt!" -ForegroundColor Red
        Write-Host "✅ Usa invece:" -ForegroundColor Green
        Write-Host "   python settings/usethis.py $pkgs" -ForegroundColor Cyan
        Write-Host ""
    } else {
        & pip.exe @args
    }
}
