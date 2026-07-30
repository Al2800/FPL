[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
$dispatcher = Join-Path $root 'scripts\run_deadline_capture_dispatch.py'
$config = Join-Path $root 'config\data_sources\2026-27-capture-scheduler.json'
foreach ($path in @($PythonPath, $dispatcher, $config)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required scheduler path is missing: $path"
    }
}

& $PythonPath $dispatcher --config $config --python $PythonPath
exit $LASTEXITCODE