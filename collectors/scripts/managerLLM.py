import subprocess
import json
import requests
import os

# הגדרות
POWERSHELL_SCRIPT = "get_processes.ps1"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" # וודא שזה המודל שהורדת ב-Ollama

def run_collector():
    print(f"[*] מפעיל את {POWERSHELL_SCRIPT}...")
    if not os.path.exists(POWERSHELL_SCRIPT):
        print(f"[-] שגיאה: הקובץ {POWERSHELL_SCRIPT} לא נמצא בתיקייה!")
        return None

    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", POWERSHELL_SCRIPT],
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if result.returncode != 0:
        print(f"[-] שגיאת PowerShell: {result.stderr}")
        return None

    try:
        data = json.loads(result.stdout.strip())
        print(f"[V] האיסוף הסתיים. נמצאו {len(data.get('InstalledApps', []))} תוכנות.")
        return data
    except Exception as e:
        print(f"[-] שגיאה בפענוח ה-JSON: {e}")
        print(f"פלט שהתקבל: {result.stdout[:100]}...")
        return None

def analyze_with_llm(app_name):
    print(f"[*] מבצע תחקיר LLM על: {app_name}...")
    prompt = f"הסבר למשתמש פשוט בעברית: מה עושה התוכנה {app_name} ואיך תוקף יכול להשתמש בה לרעה? ענה ב-2 משפטים."
    
    try:
        response = requests.post(OLLAMA_URL, 
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False}, 
            timeout=15)
        return response.json().get('response', 'אין ניתוח זמין')
    except Exception as e:
        return f"שגיאה בחיבור ל-Ollama: וודא שהתוכנה רצה."

def main():
    # 1. איסוף
    data = run_collector()
    if not data: return

    apps = data.get('InstalledApps', [])
    if not apps:
        print("[-] לא נמצאו תוכנות מותקנות.")
        return

    # 2. ניתוח (לצורך הבדיקה ננתח את 3 הראשונות שמצאנו)
    print("\n--- דו\"ח ניתוח תוכנות (לפי אפיון הפרוייקט) ---")
    for app in apps[:3]: 
        name = app.get('Name', 'Unknown')
        analysis = analyze_with_llm(name)
        print(f"\n> תוכנה: {name}")
        print(f"> ניתוח סיכון: {analysis}")
        print("-" * 30)

if __name__ == "__main__":
    main()