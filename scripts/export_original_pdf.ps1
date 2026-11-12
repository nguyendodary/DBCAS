param([Parameter(Mandatory=$true)][string]$Docx, [Parameter(Mandatory=$true)][string]$OutPdf)
$ErrorActionPreference = 'Stop'
$tmp = Join-Path $env:TEMP 'dbcas-orig'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$srcDoc = Join-Path $tmp 'source.docx'
$srcPdf = Join-Path $tmp 'source.pdf'
if (Test-Path $srcPdf) { Remove-Item $srcPdf -Force }
Write-Output "copying"
Copy-Item $Docx $srcDoc -Force
Write-Output "starting word"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.ScreenUpdating = $false
Write-Output "opening"
$doc = $word.Documents.Open($srcDoc, $false, $true, $false)
Write-Output "opened"
try {
  $doc.SaveAs2($srcPdf, 17)
  Write-Output "saved"
} finally {
  $doc.Close(0)
  $word.Quit()
}
Copy-Item $srcPdf $OutPdf -Force
Write-Output ("wrote " + $OutPdf)
