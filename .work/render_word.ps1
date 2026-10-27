param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf,
    [switch]$UpdateAndSave
)
$ErrorActionPreference = 'Stop'
$wordApp = $null
$wordDocument = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    $inputAbsolute = (Resolve-Path -LiteralPath $InputDocx).Path
    $outputAbsolute = [System.IO.Path]::GetFullPath($OutputPdf)
    $wordDocument = $wordApp.Documents.Open($inputAbsolute, $false, (-not $UpdateAndSave.IsPresent))
    if ($UpdateAndSave) {
        $wordDocument.Fields.Update() | Out-Null
        foreach ($contents in $wordDocument.TablesOfContents) { $contents.Update() }
        $wordDocument.Repaginate()
        foreach ($contents in $wordDocument.TablesOfContents) { $contents.UpdatePageNumbers() }
        $wordDocument.Save()
    }
    $wordDocument.ExportAsFixedFormat($outputAbsolute, 17)
    Write-Output ('Pages: ' + $wordDocument.ComputeStatistics(2))
    Write-Output ('PDF: ' + $outputAbsolute)
} finally {
    if ($null -ne $wordDocument) { $wordDocument.Close(0) }
    if ($null -ne $wordApp) { $wordApp.Quit() }
    if ($null -ne $wordDocument) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordDocument) }
    if ($null -ne $wordApp) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordApp) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
