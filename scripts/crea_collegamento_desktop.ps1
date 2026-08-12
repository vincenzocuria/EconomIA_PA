$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$bat = Join-Path $PSScriptRoot "avvia_ecogest.bat"
$ico = Join-Path $PSScriptRoot "ecogest.ico"
$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "EcoGest Comune.lnk"

python (Join-Path $PSScriptRoot "genera_icona_ecogest.py") | Out-Null

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($lnkPath)
$lnk.TargetPath = $bat
$lnk.WorkingDirectory = $root
$lnk.IconLocation = "$ico,0"
$lnk.Description = "Avvia EcoGest Comune e apre il browser"
$lnk.Save()

Write-Host "Collegamento creato: $lnkPath"
