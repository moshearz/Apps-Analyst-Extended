# --- הגדרות ---
# רשימת "דגלים אדומים" לזיהוי מהיר
$watchPattern = "AnyDesk|TeamViewer|RustDesk|Ammyy|VNC|RemoteDesktop|LogMeIn"

$results = New-Object System.Collections.Generic.List[PSObject]

# --- שכבה 1: Registry (מוציא את הכל - ללא סינון שמות!) ---
$registryPaths = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$regApps = Get-ItemProperty $registryPaths -ErrorAction SilentlyContinue | 
           Where-Object { $_.DisplayName -ne $null }

foreach ($app in $regApps) {
    # בודק אם התוכנה הספציפית הזו נחשבת חשודה
    $isSuspicious = $app.DisplayName -match $watchPattern
    
    $results.Add([PSCustomObject]@{ 
        Name = $app.DisplayName; 
        Source = "Registry"; 
        Status = "Installed";
        IsSuspicious = $isSuspicious  # דגל שיעזור לפייתון לזהות סיכון בקלות
    }) 
}

# --- שכבה 2: Running Processes (רק מה שחשוד ורץ כרגע) ---
$procs = Get-Process | Where-Object { $_.ProcessName -match $watchPattern } -ErrorAction SilentlyContinue
foreach ($p in $procs) { 
    $results.Add([PSCustomObject]@{ 
        Name = $p.ProcessName; 
        Source = "RunningProcess"; 
        Status = "Active";
        IsSuspicious = $true
    }) 
}

# --- שכבה 3: File System (רק מה שחשוד בתיקיות המשתמש) ---
$userPaths = @("$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop")
$suspiciousFiles = Get-ChildItem -Path $userPaths -Filter "*.exe" -Recurse -File -ErrorAction SilentlyContinue | 
                   Where-Object { $_.Name -match $watchPattern }
foreach ($f in $suspiciousFiles) { 
    $results.Add([PSCustomObject]@{ 
        Name = $f.Name; 
        Source = "FileSystem"; 
        Status = "FoundInFolder";
        IsSuspicious = $true
    }) 
}

# הצגת התוצאות
$results | Sort-Object Name -Unique | ConvertTo-Json