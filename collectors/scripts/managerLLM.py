import subprocess #Enables running PowerShell scripts (and more)
import json #For parsing JSON output from PowerShell
import requests #For interacting with the local Ollama LLM API  
import os 

# Settings
POWERSHELL_SCRIPT = "get_processes.ps1" # Ensure this filename is correct
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3" # Verified local model name

# runs the PowerShell script to collect installed applications
def run_collector():
    print(f"[*] Running collector script: {POWERSHELL_SCRIPT}...")
    
    # Check if the PowerShell script exists in the directory
    if not os.path.exists(POWERSHELL_SCRIPT):
        print(f"[-] Error: Script not found: {POWERSHELL_SCRIPT}")
        return None

    # Execute PowerShell script and capture JSON output
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", POWERSHELL_SCRIPT],
        capture_output=True, text=True, encoding='utf-8'
    )
    
    # Handle PowerShell execution errors
    if result.returncode != 0:
        print(f"[-] PowerShell Error: {result.stderr}")
        return None

    try:
        # Parse the JSON string into a Python dictionary
        data = json.loads(result.stdout.strip())
        print(f"[V] Collection complete. Found {len(data.get('InstalledApps', []))} applications.")
        return data
    except Exception as e:
        print(f"[-] JSON Parsing Error: {e}")
        print(f"Received output snippet: {result.stdout[:100]}...")
        return None

# Analyzes a given application name using the local LLM - we use the Ollama API and the model llama3
def analyze_with_llm(app_name):
    print(f"[*] Investigating app with LLM: {app_name}...")
    
    # Prompt is kept in Hebrew to satisfy the project goal of simple Hebrew explanations
    # Updated prompt for English output to avoid RTL issues in Terminal
    prompt = (
        f"Act as a cybersecurity expert. Analyze the software: '{app_name}'. "
        f"Provide a concise summary for a non-technical user in 2 sentences: "
        f"1. What is the legitimate purpose of this software? "
        f"2. How could a malicious actor misuse it (Dual-use risk)? "
        f"Keep the tone professional and clear."
    )
    
    try:
        # Send POST request to local Ollama API
        response = requests.post(OLLAMA_URL, 
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False}, 
            timeout=30) # timeout for each request - for each "Item" being analyzed
        
        if response.status_code == 200:
            return response.json().get('response', 'No analysis available.')
        else:
            return f"LLM Error: Status code {response.status_code}"
            
    except Exception as e:
        return f"Connection Error: Ensure Ollama is running at {OLLAMA_URL}. Error: {e}"

def main():
    # 1. Data Collection Phase
    data = run_collector()
    if not data: 
        print("[-] Data collection failed. Exiting.")
        return

    apps = data.get('InstalledApps', [])
    if not apps:
        print("[-] No installed applications found.")
        return

    # 2. Analysis Phase (Analyzing the first 3 apps as a sample/test)
    print("\n" + "="*50)
    print("SOFTWARE ANALYSIS REPORT (Project Specs)")
    print("="*50)
    
    for app in apps: 
        name = app.get('Name', 'Unknown')
        analysis = analyze_with_llm(name)
        
        print(f"\n> Application: {name}")
        print(f"> Risk Analysis: {analysis}")
        print("-" * 50)

if __name__ == "__main__":
    main()