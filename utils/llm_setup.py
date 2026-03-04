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
    return "gemma3:1b"  # Fallback to the default used in llm_analyzer

def check_and_pull_model(model_name=None, progress_callback=None):
    if model_name is None:
        model_name = get_model_from_analyzer()
    
    try:
        ollama.list()
    except Exception:
        return "ERROR_OLLAMA_OFFLINE"

    try:
        available_models = [m['name'] for m in ollama.list()['models']]
        if any(model_name in m for m in available_models):
            return True
    except Exception:
        pass

    try:
        if progress_callback:
            progress_callback(f"[*] Downloading '{model_name}' (2-3GB)...")
        
        current_digest = None
        for progress in ollama.pull(model_name, stream=True):
            # Extract values safely
            completed = progress.get('completed')
            total = progress.get('total')
            digest = progress.get('digest', '')
            status = progress.get('status', '')

            # Check if we have valid numbers to prevent the 'NoneType' error
            if progress_callback and completed is not None and total is not None and total > 0:
                percentage = int((completed / total) * 100)
                
                if digest != current_digest and digest:
                    progress_callback(f"    - Processing layer {digest[:12]}...")
                    current_digest = digest
                
                # Draw the bar
                bar_len = 20
                filled = int(bar_len * completed // total)
                bar = '█' * filled + '-' * (bar_len - filled)
                progress_callback(f"    [{bar}] {percentage}%", update_last=True)
            
            # If there is no numeric progress, just show the status text
            elif progress_callback and status:
                if status != "downloading": # avoid flooding the UI
                    progress_callback(f"    [*] Status: {status}")

        return True
    except Exception as e:
        return str(e)
    """
    Checks if model exists. If not, pulls it and sends updates to progress_callback.
    """
    if model_name is None:
        model_name = get_model_from_analyzer()
    
    # 1. Check if Ollama is running
    try:
        ollama.list()
    except Exception:
        return "ERROR_OLLAMA_OFFLINE"

    # 2. Check if model exists
    try:
        available_models = [m['name'] for m in ollama.list()['models']]
        if any(model_name in m for m in available_models):
            return True
    except Exception:
        pass

    # 3. Download with streaming
    try:
        if progress_callback:
            progress_callback(f"[*] Downloading '{model_name}'...")
        
        # Use the streaming API
        current_digest = None
        for progress in ollama.pull(model_name, stream=True):
            status = progress.get('status', '')
            completed = progress.get('completed', 0)
            total = progress.get('total', 0)
            digest = progress.get('digest', '')

            if total > 0 and progress_callback:
                # Update progress bar logic: only print when percentage changes or new layer starts
                percentage = int((completed / total) * 100)
                # To prevent flooding the text box, we only send updates for meaningful changes
                if digest != current_digest:
                    progress_callback(f"    - Layer {digest[:10]}...")
                    current_digest = digest
                
                # Custom visual progress bar for the text area
                bar_len = 20
                filled = int(bar_len * completed // total)
                bar = '█' * filled + '-' * (bar_len - filled)
                # We use a special 'UPDATE_LAST_LINE' signal handled in the GUI
                progress_callback(f"    [{bar}] {percentage}%", update_last=True)
                
        return True
    except Exception as e:
        return str(e)