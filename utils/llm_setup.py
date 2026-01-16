import ollama
import sys
import logging
from tqdm import tqdm  # ספרייה לפס התקדמות (pip install tqdm)

logger = logging.getLogger("LLM_Setup")

def check_and_pull_model(model_name="ministral-3:3b"):
    """
    בודק אם המודל קיים. אם לא - מוריד אותו אוטומטית.
    אם Ollama לא מותקן - מתריע למשתמש.
    """
    print(f"[*] Checking for LLM model: {model_name}...")

    # 1. בדיקה האם Ollama בכלל רץ
    try:
        ollama.list()
    except Exception as e:
        print("\n[!] Error: Could not connect to Ollama.")
        print("Please ensure Ollama is installed and running.")
        print("Download link: https://ollama.com/download")
        sys.exit(1) # עוצר את התוכנה כי אי אפשר להמשיך בלי זה

    # 2. בדיקה האם המודל כבר קיים אצל המשתמש
    try:
        available_models = [m['name'] for m in ollama.list()['models']]
        # לפעמים השם מגיע עם :latest ולפעמים בלי, נבדוק התאמה חלקית
        if any(model_name in m for m in available_models):
            print(f"[v] Model '{model_name}' is ready.")
            return True
    except Exception:
        pass

    # 3. אם הגענו לפה - המודל חסר. נוריד אותו.
    print(f"[*] Model '{model_name}' not found. Downloading now (approx 2-3GB)...")
    print("    This happens only once. Please wait...")

    try:
        # פקודת המשיכה (Pull) דרך הקוד
        # stream=True מאפשר לנו לראות התקדמות אם נרצה, כאן נעשה את זה פשוט
        ollama.pull(model_name)
        print("\n[v] Download complete! Starting analysis...")
        return True
    except Exception as e:
        print(f"\n[!] Failed to download model: {e}")
        return False