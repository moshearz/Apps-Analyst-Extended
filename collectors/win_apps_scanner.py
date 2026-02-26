import winreg
from datetime import datetime
import os
from collections import defaultdict

class WinAppsScanner:
    def __init__(self):
        # רשימת נתיבי Registry שבהם רשומות תוכנות מותקנות ב-Windows
        self.registry_paths = [
            # תוכנות 64-bit או 32-bit על מערכת 32-bit (System Wide)
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            # תוכנות 32-bit על מערכת 64-bit (System Wide)
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            # תוכנות שהותקנו עבור המשתמש הנוכחי בלבד (User Specific)
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        # רשימת תיקיות לחיפוש קבצי exe
        self.file_scan_paths = [
            os.path.expanduser("~")
        ]

    def get_base_name(self, name):
        """פונקציה לחילוץ שם בסיס לתצוגה מקובצת"""
        parts = name.split()
        if len(parts) >= 2 and any(c.isdigit() for c in parts[1]):
            # אם החלק השני מכיל ספרות (גרסה), קח את שני החלקים הראשונים
            return ' '.join(parts[:2])
        else:
            # אחרת, קח את המילה הראשונה
            return parts[0]

    def _get_registry_value(self, key, value_name):
        """פונקציית עזר לשליפת ערך בטוחה מה-Registry"""
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
        except FileNotFoundError:
            return None

    def scan(self):
        """
        הפונקציה הראשית שמבצעת את הסריקה ומחזירה שתי רשימות:
        - תוכנות מתוך ה-Registry
        - קבצי exe שנמצאו במערכת הקבצים
        כל רשימה היא מערך של dict עם מידע על האפליקציה.
        """
        registry_apps = []
        exe_apps = []
        seen_apps = set()  # למניעת כפילויות כלליות

        print("[*] Starting Windows apps scan (registry)...")

        for hive, sub_key_path in self.registry_paths:
            try:
                # פתיחת הנתיב הראשי (למשל Uninstall)
                with winreg.OpenKey(hive, sub_key_path) as parent_key:
                    # בדיקה כמה תתי-מפתחות קיימים
                    num_subkeys = winreg.QueryInfoKey(parent_key)[0]
                    
                    for i in range(num_subkeys):
                        try:
                            # קבלת שם המפתח (למשל {GUID} או שם התוכנה)
                            subkey_name = winreg.EnumKey(parent_key, i)
                            
                            # פתיחת תת-המפתח הספציפי של התוכנה
                            with winreg.OpenKey(parent_key, subkey_name) as app_key:
                                # שליפת נתונים רלוונטיים
                                display_name = self._get_registry_value(app_key, "DisplayName")
                                
                                if not display_name:
                                    continue

                                app_info = {
                                    "name": display_name,
                                    "version": self._get_registry_value(app_key, "DisplayVersion") or "Unknown",
                                    "publisher": self._get_registry_value(app_key, "Publisher") or "Unknown",
                                    "install_date": self._get_registry_value(app_key, "InstallDate") or "Unknown",
                                    "uninstall_string": self._get_registry_value(app_key, "UninstallString"),
                                    "install_location": self._get_registry_value(app_key, "InstallLocation") or "Unknown",
                                    "source_registry": sub_key_path
                                }

                                app_id = f"{app_info['name']}_{app_info['version']}"
                                if app_id not in seen_apps:
                                    registry_apps.append(app_info)
                                    seen_apps.add(app_id)

                        except OSError:
                            continue
                            
            except OSError as e:
                print(f"[!] Failed to access registry path {sub_key_path}: {e}")

        # סריקת קבצי exe במערכת הקבצים
        print("[*] Starting filesystem scan for exe files...")
        for path in self.file_scan_paths:
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.exe'):
                            full_path = os.path.join(root, file)
                            app_info = {
                                "name": os.path.splitext(file)[0],
                                "version": "Unknown",
                                "publisher": "Unknown",
                                "install_date": "Unknown",
                                "uninstall_string": None,
                                "install_location": full_path,
                                "source_registry": f"Filesystem: {full_path}"
                            }
                            app_id = f"{app_info['name']}_filesystem"
                            if app_id not in seen_apps:
                                exe_apps.append(app_info)
                                seen_apps.add(app_id)
            except OSError as e:
                print(f"[!] Failed to scan path {path}: {e}")

        print(f"[v] Scan complete. Found {len(registry_apps)} registry apps and {len(exe_apps)} exe files.")
        return registry_apps, exe_apps

# בלוק לבדיקה עצמאית של הקובץ (כשמריצים אותו ישירות)
if __name__ == "__main__":
    scanner = WinAppsScanner()
    registry, exe = scanner.scan()

    print(f"\n--- Registry Apps ({len(registry)}) ---")
    for idx, app in enumerate(registry, start=1):
        print(f"{idx}. {app['name']}")
    print(f"\n--- EXE Files ({len(exe)}) ---")
    for idx, app in enumerate(exe, start=1):
        print(f"{idx}. {app['name']}")

    # קיבוץ יישומים לפי שם בסיס (on registry only)
    grouped = defaultdict(list)
    for app in registry:
        base = scanner.get_base_name(app['name'])
        grouped[base].append(app)
    
    # שמירה לקובץ טקסט בתיקיית output
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "installed_apps.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Found {len(grouped)} Application Groups\n\n")
        for base in sorted(grouped.keys()):
            f.write(f"[*] {base}\n")
    
    print(f"\nGrouped list saved to {output_file}")
