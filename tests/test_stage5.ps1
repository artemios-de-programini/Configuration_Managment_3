<#
.SYNOPSIS
    Демонстрация этапа 5 проекта УВМ (вариант №8).
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
    Write-Host '=== ТЕСТ: Этап 5 ==='
    Write-Host ''
    Write-Host '--- 1. Тестовая задача: два вектора длины 6 ---'
    Invoke-Python @('src/main.py', 'tests/vector_equal_6.csv', 'output/vector_equal_6.bin')
    Invoke-Python @('src/interpreter.py', 'output/vector_equal_6.bin', 'output/vector_equal_6.xml', '100:105')
    Write-Host ''
    Write-Host '--- 2. Пример 1: векторы без совпадений ---'
    Invoke-Python @('src/main.py', 'tests/example_1.csv', 'output/example_1.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_1.bin', 'output/example_1.xml', '300:305')
    Write-Host ''
    Write-Host '--- 3. Пример 2: копия и оригинал ---'
    Invoke-Python @('src/main.py', 'tests/example_2.csv', 'output/example_2.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_2.bin', 'output/example_2.xml', '800:805')
    Write-Host ''
    Write-Host '--- 4. Пример 3: сравнение со сдвигом ---'
    Invoke-Python @('src/main.py', 'tests/example_3.csv', 'output/example_3.bin')
    Invoke-Python @('src/interpreter.py', 'output/example_3.bin', 'output/example_3.xml', '980:985')
    Write-Host ''
    Write-Host 'Готово: результаты в каталоге output.'
}
finally {
    Pop-Location
}
exit 0
