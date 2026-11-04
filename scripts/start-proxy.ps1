$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskMitmweb = Join-Path $taskProjectRoot '.tools\Scripts\mitmweb.exe'
if (-not (Test-Path -LiteralPath $taskMitmweb)) {
    throw 'mitmweb is missing from .tools. See README.md.'
}
foreach ($taskPort in @(58888, 8081)) {
    $taskPortCheck = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $taskPort)
    try { $taskPortCheck.Start() } catch {
        throw "Port $taskPort is already in use. Stop the existing capture proxy before starting this one."
    } finally { $taskPortCheck.Stop() }
}
$taskCaptureRoot = Join-Path $env:LOCALAPPDATA 'CS146S\captures'
New-Item -ItemType Directory -Path $taskCaptureRoot -Force | Out-Null
$taskSavedPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& git -C $taskCaptureRoot rev-parse --show-toplevel 2>$null | Out-Null
$taskGitExit = $LASTEXITCODE
$ErrorActionPreference = $taskSavedPreference
if ($taskGitExit -eq 0) {
    throw 'Capture storage must be outside all Git repositories.'
}
$taskRunName = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$taskRunDirectory = Join-Path $taskCaptureRoot $taskRunName
New-Item -ItemType Directory -Path $taskRunDirectory | Out-Null
$taskFlowFile = Join-Path $taskRunDirectory 'session.flows'
$taskConfDirectory = Join-Path $env:LOCALAPPDATA 'CS146S\mitmproxy'
Write-Host ('Private local capture: ' + $taskFlowFile)
Write-Host 'Upstream: https://api.deepseek.com (client requests must include /anthropic).'
Write-Host 'Use the local UI link printed below. Ctrl+C stops the proxy.'
& $taskMitmweb --listen-host 127.0.0.1 --listen-port 58888 --web-host 127.0.0.1 --web-port 8081 --no-web-open-browser --set "confdir=$taskConfDirectory" --set connection_strategy=lazy --mode reverse:https://api.deepseek.com -s (Join-Path $PSScriptRoot 'deepseek_proxy.py') -w $taskFlowFile
