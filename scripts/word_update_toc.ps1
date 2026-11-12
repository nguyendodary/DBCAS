param([string]$Name, [switch]$SkipPdf)
$ErrorActionPreference = "Stop"
$dir = "C:\tmp\dbcas_word"
$path = Join-Path $dir "$Name.docx"
$pdf = Join-Path $dir "$Name.pdf"

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

Get-Process WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.UpdateLinksAtOpen = $false
[Console]::WriteLine("word started")
$doc = Retry-Com { $word.Documents.Open($path, $false, $false, $false) }
[Console]::WriteLine("opened")
[Console]::WriteLine("toc count=" + $doc.TablesOfContents.Count + " tof count=" + $doc.TablesOfFigures.Count)
foreach ($tof in $doc.TablesOfFigures) {
    $code = Retry-Com { $tof.Range.Fields.Item(1).Code.Text }
    Retry-Com { $tof.Update() }
    [Console]::WriteLine("list rebuilt: $code")
}
Retry-Com { $doc.Repaginate() }
foreach ($toc in $doc.TablesOfContents) {
    Retry-Com { $toc.UpdatePageNumbers() }
    [Console]::WriteLine("toc page numbers updated")
}
Retry-Com { $doc.Repaginate() }
[Console]::WriteLine("fields updated")
Retry-Com { $doc.Save() }
[Console]::WriteLine("saved")
if (-not $SkipPdf) {
    Retry-Com { $doc.SaveAs2($pdf, 17) }
    [Console]::WriteLine("pdf exported")
}
[Console]::WriteLine("pages=" + (Retry-Com { $doc.ComputeStatistics(2) }))
Retry-Com { $doc.Close(0) }
$word.Quit()
[Console]::WriteLine("done")
