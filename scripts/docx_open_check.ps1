param([string[]]$Docs)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
foreach ($d in $Docs) {
  $doc = $word.Documents.Open($d, $false, $true, $false)
  $pages = $doc.ComputeStatistics(2)
  Write-Output ("OK " + (Split-Path $d -Leaf) + " pages=" + $pages + " words=" + $doc.ComputeStatistics(0))
  $doc.Close(0)
}
$word.Quit()
