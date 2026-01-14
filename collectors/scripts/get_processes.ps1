# PowerShell script to get running processes or specific app details
Get-Process | Select-Object Name, Id, Path
# get_processes.ps1
# return:
# Registry installed apps 
#running processes 
# EXEs 

# וגם לא “מאבד” פריטים בגלל Sort-Unique על Name בלבד.

$results = [System.Collections.Generic.List[object]]::new()

# Registry
$regPaths = @(
  "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$installedApps =
  Get-ItemProperty $regPaths -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName } |
  ForEach-Object {
    [PSCustomObject]@{
      Name      = $_.DisplayName
      Version   = $_.DisplayVersion
      Publisher = $_.Publisher
      InstallLocation = $_.InstallLocation
      Source    = "Registry"
      Status    = "Installed"
    }
  }

# Running processes (all) 
$runningProcesses =
  Get-Process -ErrorAction SilentlyContinue |
  ForEach-Object {
    # חלק מהתהליכים לא מאפשרים קריאה של Path בלי הרשאות, אז נעטוף ב-try/catch
    $path = $null
    try { $path = $_.Path } catch { $path = $null }

    [PSCustomObject]@{
      Name   = $_.ProcessName
      Id     = $_.Id
      Path   = $path
      Source = "RunningProcess"
      Status = "Active"
    }
  }

# ---------- 3) EXE scan in common user folders ----------
$userPaths = @(
  "$env:USERPROFILE\Downloads",
  "$env:USERPROFILE\Desktop",
  "$env:USERPROFILE\Documents"
)

$foundExes =
  Get-ChildItem -Path $userPaths -Filter "*.exe" -Recurse -File -ErrorAction SilentlyContinue |
  ForEach-Object {
    [PSCustomObject]@{
      Name   = $_.Name
      Path   = $_.FullName
      Size   = $_.Length
      LastWriteTime = $_.LastWriteTime
      Source = "FileSystem"
      Status = "FoundInFolder"
    }
  }

# ---------- 4) De-dup נכון (לא רק לפי Name) ----------
# Registry: ייחוד לפי Name+Version+Publisher
$installedAppsUnique = $installedApps |
  Sort-Object Name, Version, Publisher -Unique

# Running: ייחוד לפי Name+Id (כי אותו שם יכול להופיע כמה פעמים)
$runningProcessesUnique = $runningProcesses |
  Sort-Object Name, Id -Unique

# FileSystem: ייחוד לפי Full Path
$foundExesUnique = $foundExes |
  Sort-Object Path -Unique

# ---------- 5) Counts / Summary ----------
$summary = [PSCustomObject]@{
  Total = ($installedAppsUnique.Count + $runningProcessesUnique.Count + $foundExesUnique.Count)
  BySource = [PSCustomObject]@{
    Registry       = $installedAppsUnique.Count
    RunningProcess = $runningProcessesUnique.Count
    FileSystem     = $foundExesUnique.Count
  }
}

# ---------- 6) Output (JSON אחד מסודר) ----------
$out = [PSCustomObject]@{
  Summary         = $summary
  InstalledApps   = $installedAppsUnique
  RunningProcesses= $runningProcessesUnique
  FoundExecutables= $foundExesUnique
}

$out | ConvertTo-Json -Depth 6
