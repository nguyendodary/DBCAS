# Read heading and caption page numbers from the rendered Word layout.
# Usage: powershell -File scripts/word_page_map.ps1 -Src <docx> -Out <json>
param(
  [Parameter(Mandatory=$true)][string]$Src,
  [Parameter(Mandatory=$true)][string]$Out
)

$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($Src, $false, $true)
$items = New-Object System.Collections.ArrayList
$count = 0
foreach ($p in $doc.Paragraphs) {
  $style = ''
  try { $style = $p.Style.NameLocal } catch {}
  $text = ''
  try { $text = $p.Range.Text.Trim() } catch {}
  if (-not $text) { continue }
  $kind = $null
  if ($style -like 'Heading 1*') { $kind = 'h1' }
  elseif ($style -like 'Heading 2*') { $kind = 'h2' }
  elseif ($text -match '^(Table|Figure)\s+(A\.)?\d+(\.|:|\s)' -and $text.Length -lt 320 -and $style -notlike '*TOC*' -and $style -notlike '*table of figures*') {
    $kind = 'caption'
  }
  if ($kind) {
    $page = 0
    try { $page = [int]$p.Range.Information(3) } catch {}
    [void]$items.Add([pscustomobject]@{ kind = $kind; page = $page; style = $style; text = $text })
    $count++
  }
}
$doc.Close($false)
$word.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
$json = $items | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("{0}: {1} items" -f (Split-Path $Src -Leaf), $count)
