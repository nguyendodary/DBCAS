param(
  [string]$Name = 'ProposalDocument'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$final = Join-Path $root 'docs\submission\final'
$rendered = Join-Path $final 'rendered'
New-Item -ItemType Directory -Force -Path $rendered | Out-Null
$src = Join-Path $final ("C1SE.70_{0}_DBCAS_ver1.3.docx" -f $Name)
$pdf = Join-Path $rendered ("C1SE.70_{0}_DBCAS_ver1.3.pdf" -f $Name)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateFieldsAtPrint = $false
$word.Options.UpdateLinksAtOpen = $false
try {
  $doc = $word.Documents.Open($src, $false, $true, $false)
  try {
    Write-Output "opened pages=$($doc.ComputeStatistics(2))"
    $doc.SaveAs2($pdf, 17)
    Write-Output "saved $pdf"
  } finally { $doc.Close(0) }
} finally { $word.Quit() }
