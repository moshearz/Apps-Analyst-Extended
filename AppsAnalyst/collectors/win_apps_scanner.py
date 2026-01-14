import subprocess
import json
import os

def scan_installed_apps():
    # נתיב לסקריפט שיצרתם
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'get_sys_info_apps.ps1')
    
    # הרצה תחת עקרון מזעור הזכויות - הרצה כמשתמש רגיל [cite: 2098]
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None