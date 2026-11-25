<#
.SYNOPSIS
    Запуск проверки проекта УВМ (вариант №8) под Windows PowerShell.
.DESCRIPTION
    Зеркало run.sh: собирает программы, выполняет их, пишет дампы
    в output/ и запускает автотесты.
.EXAMPLE
    .\tests\run.ps1
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
    Invoke-Python @('src/main.py', 'tests/spec_test.csv', 'output/spec_test.bin', '--test')
    Invoke-Python @('src/main.py', 'tests/copy_array.csv', 'output/copy_array.bin')
    Invoke-Python @('src/interpreter.py', 'output/copy_array.bin', 'output/copy_array.xml', '800:807')
    Invoke-Python @('src/main.py', 'tests/eq_test.csv', 'output/eq_test.bin')
    Invoke-Python @('src/interpreter.py', 'output/eq_test.bin', 'output/eq_test.xml', '30:32')
    Invoke-Python @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
}
finally {
    Pop-Location
}
