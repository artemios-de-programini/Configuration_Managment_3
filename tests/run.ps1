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
    Invoke-Python @('src/main.py', 'tests/vector_equal_6.csv', 'output/vector.bin')
    Invoke-Python @('src/interpreter.py', 'output/vector.bin', 'output/vector.xml', '100:105')
    Invoke-Python @('src/main.py', 'tests/example_1.csv', 'output/example_1.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_1.bin', 'output/example_1.xml', '300:305')
    Invoke-Python @('src/main.py', 'tests/example_2.csv', 'output/example_2.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_2.bin', 'output/example_2.xml', '800:805')
    Invoke-Python @('src/main.py', 'tests/example_3.csv', 'output/example_3.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_3.bin', 'output/example_3.xml', '980:985')
    Invoke-Python @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
}
finally {
    Pop-Location
}
