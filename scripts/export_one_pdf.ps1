# Export one v1.2 Word document to PDF via Word 16 COM.
# Word's PDF export hangs when the .docx path contains spaces, so the file is
# copied to a short temporary path first and the PDF is copied back.
param([Parameter(Mandatory=$true)][string]$Name)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$aca = Join-Path $root 'docs/academic'
$out = Join-Path $root '_review/docx-work/pdf'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$tmp = Join-Path $env:TEMP 'dbcas-word-export'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$srcDoc = Join-Path $tmp 'source.docx'
$srcPdf = Join-Path $tmp 'source.pdf'
Copy-Item (Join-Path $aca $Name) $srcDoc -Force
Write-Output ("START " + $Name)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateFieldsAtPrint = $false
try {
  $doc = $word.Documents.Open($srcDoc, $false, $true, $false)
  try {
    $pages = $doc.ComputeStatistics(2)
    $doc.ExportAsFixedFormat($srcPdf, 17)
    Write-Output ("{0}: pages={1}" -f $Name, $pages)
  } finally { $doc.Close(0) }
} finally { $word.Quit() }
Copy-Item $srcPdf (Join-Path $out ($Name -replace '\.docx$', '.pdf')) -Force
Write-Output DONE
