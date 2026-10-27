param([Parameter(Mandatory=$true)][string]$InputDocx)
$ErrorActionPreference = 'Stop'
$auditWord = $null
$auditDocument = $null
try {
    $auditWord = New-Object -ComObject Word.Application
    $auditWord.Visible = $false
    $auditWord.DisplayAlerts = 0
    $auditWord.AutomationSecurity = 3
    $auditDocument = $auditWord.Documents.Open((Resolve-Path -LiteralPath $InputDocx).Path, $false, $true)
    $auditDocument.Repaginate()
    $auditRows = @()
    foreach ($paragraph in $auditDocument.Paragraphs) {
        $styleName = $paragraph.Range.Style.NameLocal
        if ($styleName -in @('Course Heading 1', 'Course Heading 2', 'Course Introduction', 'Course References', 'Course Figure', 'Course Caption')) {
            $startRange = $paragraph.Range.Duplicate
            $startRange.Collapse(1)
            $auditRows += [pscustomobject]@{
                Kind = $styleName
                Text = $paragraph.Range.Text.Trim()
                StartPage = $startRange.Information(3)
                Y = $startRange.Information(6)
                Before = $paragraph.Format.SpaceBefore
                After = $paragraph.Format.SpaceAfter
                PageBreak = $paragraph.Format.PageBreakBefore
            }
        }
    }
    foreach ($table in $auditDocument.Tables) {
        $startRange = $table.Range.Duplicate
        $startRange.Collapse(1)
        $endRange = $table.Range.Duplicate
        $endRange.SetRange($table.Range.End - 1, $table.Range.End - 1)
        $afterRange = $auditDocument.Range($table.Range.End, $auditDocument.Content.End)
        $afterParagraph = $afterRange.Paragraphs.Item(1)
        $auditRows += [pscustomobject]@{
            Kind = 'Table'
            Text = $table.Cell(1,1).Range.Text.Trim()
            StartPage = $startRange.Information(3)
            EndPage = $endRange.Information(3)
            AfterPage = $afterParagraph.Range.Information(3)
            AfterText = $afterParagraph.Range.Text.Trim()
        }
    }
    $json = $auditRows | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'spacing-native-audit.json'), $json, [System.Text.UTF8Encoding]::new($false))
    $json
} finally {
    if ($null -ne $auditDocument) { $auditDocument.Close(0) }
    if ($null -ne $auditWord) { $auditWord.Quit() }
    if ($null -ne $auditDocument) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($auditDocument) }
    if ($null -ne $auditWord) { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($auditWord) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
