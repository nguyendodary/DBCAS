param(
  [Parameter(Mandatory = $true)][string]$Path,
  [string]$Pdf = "",
  [switch]$SkipSave
)
$ErrorActionPreference = "Stop"

function Retry-Com([scriptblock]$Block, [int]$Tries = 240) {
    for ($i = 0; $i -lt $Tries; $i++) {
        try { return & $Block }
        catch [System.Runtime.InteropServices.COMException] {
            $hr = $_.Exception.HResult
            if ($hr -eq -2147418111 -or $hr -eq -2147417846) {
                Start-Sleep -Milliseconds 500
                continue
            }
            throw
        }
    }
    throw "COM retry exhausted"
}

$full = (Resolve-Path -LiteralPath $Path).Path
if (-not $Pdf) { $Pdf = [System.IO.Path]::ChangeExtension($full, ".pdf") }
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.Options.UpdateLinksAtOpen = $false
    $doc = Retry-Com { $word.Documents.Open($full, $false, $false, $false) }
    foreach ($tof in $doc.TablesOfFigures) {
        Retry-Com { $tof.Update() } | Out-Null
    }
    Retry-Com { $doc.Fields.Update() } | Out-Null
    Retry-Com { $doc.Repaginate() } | Out-Null
    foreach ($toc in $doc.TablesOfContents) {
        Retry-Com { $toc.Update() } | Out-Null
    }
    Retry-Com { $doc.Repaginate() } | Out-Null
    if (-not $SkipSave) {
        Retry-Com { $doc.Save() } | Out-Null
    }
    Retry-Com { $doc.SaveAs2($Pdf, 17) } | Out-Null
    $pages = Retry-Com { $doc.ComputeStatistics(2) }
    $words = Retry-Com { $doc.ComputeStatistics(0) }
    Write-Output ("PAGES=" + $pages)
    Write-Output ("WORDS=" + $words)
    Write-Output ("PDF=" + $Pdf)
    Retry-Com { $doc.Close(0) } | Out-Null
    $doc = $null
}
finally {
    if ($doc -ne $null) { try { $doc.Close(0) | Out-Null } catch {} }
    if ($word -ne $null) { try { $word.Quit() } catch {} }
}
