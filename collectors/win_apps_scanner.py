import winreg
import logging
from datetime import datetime

# מנסים לייבא את ה-logger של הפרוייקט, אם נכשל (בהרצה עצמאית) מגדירים logger בסיסי
try:
    from utils.logger import setup_logger
    logger = setup_logger()
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("WinAppsScanner")

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

    def _get_registry_value(self, key, value_name):
        """פונקציית עזר לשליפת ערך בטוחה מה-Registry"""
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
        except FileNotFoundError:
            return None

    def scan(self):
        """
        הפונקציה הראשית שמבצעת את הסריקה ומחזירה רשימת תוכנות.
        """
        installed_apps = []
        seen_apps = set() # למניעת כפילויות

        logger.info("Starting Windows apps scan...")

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
                                
                                # אנחנו מעוניינים רק ברשומות שיש להן שם תצוגה
                                if not display_name:
                                    continue

                                # יצירת אובייקט מידע
                                app_info = {
                                    "name": display_name,
                                    "version": self._get_registry_value(app_key, "DisplayVersion") or "Unknown",
                                    "publisher": self._get_registry_value(app_key, "Publisher") or "Unknown",
                                    "install_date": self._get_registry_value(app_key, "InstallDate") or "Unknown",
                                    "uninstall_string": self._get_registry_value(app_key, "UninstallString"),
                                    "source_registry": sub_key_path
                                }

                                # בדיקת כפילויות (לפי שם + גרסה)
                                app_id = f"{app_info['name']}_{app_info['version']}"
                                if app_id not in seen_apps:
                                    installed_apps.append(app_info)
                                    seen_apps.add(app_id)

                        except OSError:
                            # התעלמות ממפתחות שלא ניתן לקרוא
                            continue
                            
            except OSError as e:
                logger.error(f"Failed to access registry path {sub_key_path}: {e}")

        logger.info(f"Scan complete. Found {len(installed_apps)} applications.")
        return installed_apps

# בלוק לבדיקה עצמאית של הקובץ (כשמריצים אותו ישירות)
if __name__ == "__main__":
    scanner = WinAppsScanner()
    apps = scanner.scan()
    
    print(f"\n--- Found {len(apps)} Applications ---")
    # הדפסה של 10 התוצאות הראשונות לדוגמה
    for app in apps[:10]:
        print(f"[*] {app['name']} (v{app['version']}) - {app['publisher']}")