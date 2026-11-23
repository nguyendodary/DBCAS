param(
  [Parameter(Mandatory=$true)][string]$Docx,
  [Parameter(Mandatory=$true)][string]$Pdf
)
$ErrorActionPreference = 'Stop'
$tmp = Join-Path $env:TEMP 'dbcas-docx-render'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$src = Join-Path $tmp 'source.docx'
$outPdf = Join-Path $tmp 'source.pdf'
Copy-Item $Docx $src -Force
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateFieldsAtPrint = $false
try {
  $doc = $word.Documents.Open($src, $false, $true, $false)
  try {
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($outPdf, 17)
  } finally { $doc.Close(0) }
} finally { $word.Quit() }
Copy-Item $outPdf $Pdf -Force
Write-Output ("wrote " + $Pdf)
