# collector.ps1
$regPaths = @(
  "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$installedApps = Get-ItemProperty $regPaths -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName } |
  ForEach-Object {
    [PSCustomObject]@{
      Name      = $_.DisplayName
      Version   = $_.DisplayVersion
      Publisher = $_.Publisher
      Source    = "Registry"
    }
  }

$runningProcesses = Get-Process -ErrorAction SilentlyContinue |
  ForEach-Object {
    [PSCustomObject]@{
      Name   = $_.ProcessName
      Id     = $_.Id
      Source = "RunningProcess"
    }
  }

# סינון כפילויות
$installedAppsUnique = $installedApps | Sort-Object Name, Version -Unique
$runningProcessesUnique = $runningProcesses | Sort-Object Name, Id -Unique

$out = [PSCustomObject]@{
  InstalledApps   = $installedAppsUnique
  RunningProcesses= $runningProcessesUnique
}

# זו חייבת להיות ההדפסה היחידה בקובץ!
$out | ConvertTo-Json -Depth 6