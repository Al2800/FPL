[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [ValidatePattern('^FPL Deadline-Aware Capture$')]
    [string]$TaskName = 'FPL Deadline-Aware Capture'
)

$ErrorActionPreference = 'Stop'
& schtasks.exe /Query /TN $TaskName /FO LIST | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Output "No scheduled task named '$TaskName' is registered."
    exit 0
}
if ($PSCmdlet.ShouldProcess($TaskName, 'Remove the named deadline-aware local scheduler')) {
    & schtasks.exe /Delete /TN $TaskName /F
    if ($LASTEXITCODE -ne 0) {
        throw "schtasks.exe could not remove '$TaskName'."
    }
}
Write-Output "Removed $TaskName. No evidence artifacts or scheduler state were deleted."