param(
    [string]$SettingsFile = (Join-Path $env:USERPROFILE '.claude\settings-deepseek.json')
)

$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $SettingsFile -PathType Leaf)) {
    throw 'DeepSeek settings file not found. Pass its path with -SettingsFile.'
}
try {
    # Bypass Windows proxy settings for this loopback-only probe.
    $taskProxyIdentity = & curl.exe --noproxy '*' --max-time 3 --fail --silent --show-error 'http://127.0.0.1:58888/_cs146s/upstream'
    if ($LASTEXITCODE -ne 0 -or $taskProxyIdentity -ne 'https://api.deepseek.com/anthropic') {
        throw 'Unexpected proxy upstream.'
    }
} catch {
    throw 'The CS146S DeepSeek proxy is not ready. Stop any old proxy and start scripts/start-proxy.ps1 in another terminal first.'
}
$taskClaude = Get-Command claude.cmd -ErrorAction SilentlyContinue
if (-not $taskClaude) { $taskClaude = Get-Command claude.exe -ErrorAction Stop }
$taskSessionDirectory = Join-Path ([IO.Path]::GetTempPath()) ('cs146s-claude-' + [Guid]::NewGuid().ToString('N'))
$taskSessionSettings = Join-Path $taskSessionDirectory 'settings.json'
$taskSavedEnvironment = @{}
foreach ($taskKey in @('ANTHROPIC_BASE_URL', 'NO_PROXY')) {
    $taskSavedEnvironment[$taskKey] = [Environment]::GetEnvironmentVariable($taskKey, 'Process')
}
Push-Location -LiteralPath $taskProjectRoot
try {
    $env:ANTHROPIC_BASE_URL = 'http://127.0.0.1:58888/anthropic'
    $env:NO_PROXY = (@($env:NO_PROXY, '127.0.0.1', 'localhost') | Where-Object { $_ }) -join ','
    # The selected profile may contain credentials; protect its temporary copy before writing it.
    New-Item -ItemType Directory -Path $taskSessionDirectory | Out-Null
    $taskAcl = New-Object System.Security.AccessControl.DirectorySecurity
    $taskAcl.SetAccessRuleProtection($true, $false)
    $taskRule = New-Object System.Security.AccessControl.FileSystemAccessRule([System.Security.Principal.WindowsIdentity]::GetCurrent().User, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $taskAcl.AddAccessRule($taskRule)
    Set-Acl -LiteralPath $taskSessionDirectory -AclObject $taskAcl
    try {
        $taskSettings = Get-Content -LiteralPath $SettingsFile -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw 'Selected settings file could not be read as JSON. Contents omitted.'
    }
    if ($null -eq $taskSettings.env) {
        $taskSettings | Add-Member -MemberType NoteProperty -Name env -Value ([pscustomobject]@{})
    }
    $taskSettings.env | Add-Member -MemberType NoteProperty -Name ANTHROPIC_BASE_URL -Value $env:ANTHROPIC_BASE_URL -Force
    $taskSettings | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $taskSessionSettings -Encoding UTF8
    Write-Host ('Profile: ' + $SettingsFile)
    Write-Host ('This session: ' + $env:ANTHROPIC_BASE_URL + ' -> https://api.deepseek.com/anthropic')
    & $taskClaude.Source --settings $taskSessionSettings --safe-mode --strict-mcp-config
} finally {
    foreach ($taskKey in $taskSavedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($taskKey, $taskSavedEnvironment[$taskKey], 'Process')
    }
    Pop-Location
    if (Test-Path -LiteralPath $taskSessionSettings) { Remove-Item -LiteralPath $taskSessionSettings }
    if (Test-Path -LiteralPath $taskSessionDirectory) { Remove-Item -LiteralPath $taskSessionDirectory }
}
