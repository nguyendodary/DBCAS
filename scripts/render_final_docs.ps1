param(
  [string[]]$Names = @('ProposalDocument','ArchitectureDesign','DatabaseDesign','CodeStandards','TechnicalReport')
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$final = Join-Path $root 'docs\submission\final'
$rendered = Join-Path $final 'rendered'
New-Item -ItemType Directory -Force -Path $rendered | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateFieldsAtPrint = $false
$word.Options.UpdateLinksAtOpen = $false
$word.Options.WarnBeforeSavingPrintingSendingMarkup = $false
try {
  foreach ($name in $Names) {
    $src = Join-Path $final ("C1SE.70_{0}_DBCAS_ver1.3.docx" -f $name)
    $pdf = Join-Path $rendered ("C1SE.70_{0}_DBCAS_ver1.3.pdf" -f $name)
    if (-not (Test-Path $src)) { throw "missing $src" }
    $doc = $word.Documents.Open($src, $false, $false, $false)
    try {
      foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
      foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
      $doc.Repaginate()
      $doc.Save()
      $doc.ExportAsFixedFormat($pdf, 17)
      Write-Output ("rendered {0} pages={1}" -f $name, $doc.ComputeStatistics(2))
    } finally { $doc.Close(0) }
  }
} finally {
  $word.Quit()
}
