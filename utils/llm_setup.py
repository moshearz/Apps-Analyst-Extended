import ollama
import sys
import logging
from tqdm import tqdm  # ספרייה לפס התקדמות (pip install tqdm)

logger = logging.getLogger("LLM_Setup")

# Extract model name from llm_analyzer to ensure consistency
def get_model_from_analyzer():
    """Extract the model name used in llm_analyzer.py"""
    try:
        from analysis.llm_analyzer import sendToOllama
        import inspect
        source = inspect.getsource(sendToOllama)
        # Look for model="..." in the source code
        import re
        match = re.search(r'model="([^"]+)"', source)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "llama3.2:1b"  # Fallback to the default used in llm_analyzer

def check_and_pull_model(model_name=None):
    """
    בודק אם המודל קיים. אם לא - מוריד אותו אוטומטית.
    אם Ollama לא מותקן - מתריע למשתמש.
    אם לא מסופק model_name - משולף אותו מ-llm_analyzer
    """
    # If no model specified, extract from llm_analyzer
    if model_name is None:
        model_name = get_model_from_analyzer()
    
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