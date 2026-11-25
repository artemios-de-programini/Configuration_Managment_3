<#
.SYNOPSIS
    Демонстрация этапа 3 проекта УВМ (вариант №8).
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
    Write-Host '=== ТЕСТ: Этап 3 ==='
    Write-Host ''
    Write-Host '--- 1. Копирование массива ---'
    Invoke-Python @('src/main.py', 'tests/copy_array.csv', 'output/copy_array.bin')
    Invoke-Python @('src/interpreter.py', 'output/copy_array.bin', 'output/copy_array.xml', '800:807')
    Write-Host ''
    Write-Host 'Готово: результаты в каталоге output.'
}
finally {
    Pop-Location
}
exit 0
