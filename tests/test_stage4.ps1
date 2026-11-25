<#
.SYNOPSIS
    Демонстрация этапа 4 проекта УВМ (вариант №8).
.DESCRIPTION
    Запускает программы этапа и складывает результаты в output/.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$Python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }

function Invoke-Python([string[]]$StepArgs) {
    & $script:Python @StepArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Команда завершилась с кодом $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path 'output' | Out-Null
    Write-Host '=== ТЕСТ: Этап 4 ==='
    Write-Host ''
    Write-Host '--- 1. Операция сравнения == ---'
    Invoke-Python @('src/main.py', 'tests/eq_test.csv', 'output/eq_test.bin')
    Invoke-Python @('src/interpreter.py', 'output/eq_test.bin', 'output/eq_test.xml', '30:32')
    Write-Host ''
    Write-Host 'Готово: результаты в каталоге output.'
}
finally {
    Pop-Location
}
exit 0
