param([string]$Pdf, [string]$Out, [int]$Pages = 3)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1)
$asTaskAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and -not $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
} | Select-Object -First 1)
function Await($op, $resultType) {
  if ($resultType -eq [System.Object]) {
    $task = $asTaskAction.Invoke($null, @($op))
  } else {
    $task = $asTaskGeneric.MakeGenericMethod($resultType).Invoke($null, @($op))
  }
  $task.GetAwaiter().GetResult()
}
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$pdfType = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$fileType = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$streamType = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$file = Await ($fileType::GetFileFromPathAsync($Pdf)) ([Windows.Storage.StorageFile])
$doc = Await ($pdfType::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
Write-Output ("pdf pages=" + $doc.PageCount)
$n = [Math]::Min($Pages, $doc.PageCount)
for ($i = 0; $i -lt $n; $i++) {
  $page = $doc.GetPage($i)
  $stream = New-Object $streamType
  Await ($page.RenderToStreamAsync($stream)) ([System.Object]) | Out-Null
  $bytes = New-Object byte[] $stream.Size
  $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
  Await ($reader.LoadAsync([uint32]$stream.Size)) ([uint32]) | Out-Null
  $reader.ReadBytes($bytes)
  $path = Join-Path $Out ("page-{0:D2}.png" -f ($i + 1))
  [System.IO.File]::WriteAllBytes($path, $bytes)
  $stream.Dispose()
  Write-Output ("rendered " + $path + " " + $bytes.Length)
}
