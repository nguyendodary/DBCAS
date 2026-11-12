param(
  [Parameter(Mandatory=$true)][string]$Docx,
  [Parameter(Mandatory=$true)][string]$Out
)
$ErrorActionPreference = 'Stop'
$tmp = Join-Path $env:TEMP 'dbcas-fields'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$src = Join-Path $tmp 'fields.docx'
Copy-Item $Docx $src -Force
Write-Output 'opening'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($src, $false, $false, $false)
Write-Output 'updating'
$doc.Fields.Update() | Out-Null
foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
$doc.Repaginate()
Write-Output 'saving'
$doc.Save()
$doc.Close(0)
$word.Quit()
Copy-Item $src $Out -Force
Write-Output ('wrote ' + $Out)
