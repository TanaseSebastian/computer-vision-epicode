param(
    [string]$CsvPath = "samples.csv",
    [double]$Threshold = 0.363
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

.\.venv\Scripts\python.exe scripts\validate_dataset.py $CsvPath
.\.venv\Scripts\python.exe evaluate.py $CsvPath --threshold $Threshold --output evaluation_results.json --report docs\evaluation_report.md --plots-dir docs\figures --update-technical-analysis
.\.venv\Scripts\python.exe scripts\export_technical_pdf.py

Write-Host "Evaluation complete. Review docs\technical_analysis.pdf and docs\evaluation_report.md."
