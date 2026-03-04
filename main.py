import sys
import subprocess

# from config import load_config

# dummy constants for debug substitutions


DUMMY_REGISTRY_APPS = [{"name": "checkpointVPN", "version": "1.0"},{"name": "teamviewer", "version": "1.0"}, {"name": "vnc", "version": "2.0"}]
DUMMY_EXE_APPS = [{"name": "dummy.exe", "install_location": "C:\\dummy.exe"}]
DUMMY_WEB_INFO = "- Title: Dummy\n  Info: No real data\n"
DUMMY_LLM_RESPONSE = "Remote Administration: no\nRemote File Sharing: no\nKeylogging: no\nServer Hosting: no"

def install_missing_requirements():
    """Check requirements and install missing packages without pkg_resources.
    
    Uses importlib.metadata (standard library 3.8+) to check installed packages.
    Falls back to direct import attempts if metadata is unavailable.
    """
    requirements_file = "requirements.txt"
    
    try:
        with open(requirements_file, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        missing = []
        for requirement in requirements:
            # Extract package name (handle ==, >=, <= operators)
            pkg_name = requirement.split("==")[0].split(">=")[0].split("<=")[0].strip()
            
            try:
                # Try importlib.metadata first (Python 3.8+)
                try:
                    from importlib import metadata
                    metadata.version(pkg_name)
                except (ImportError, Exception):
                    # Fallback: try direct import
                    __import__(pkg_name)
            except Exception:
                missing.append(requirement)
        
        if missing:
            print(f"[*] Missing packages found: {missing}. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[*] All packages installed successfully.")
        else:
            print("[*] All requirements are already met.")
            
    except FileNotFoundError:
        print("[!] requirements.txt not found. Skipping auto-install.")
    except Exception as e:
        print(f"[!] Auto-install failed: {e}")

def setup_llm():
    # Initialize LLM: check and pull model if needed
    from utils.llm_setup import check_and_pull_model
    print("[i] Setting up LLM...")
    return check_and_pull_model()


def scan_apps():
    from collectors.win_apps_scanner import WinAppsScanner
    scanner = WinAppsScanner()
    return scanner.scan()


def select_app(registry_apps, exe_apps):
    app_to_analyze = None
    if registry_apps or exe_apps:
        print("\nRegistry applications:")
        for idx, app in enumerate(registry_apps, start=1):
            print(f"  {idx}. {app['name']}")
        print("\nExecutable files:")
        for idx, app in enumerate(exe_apps, start=1):
            print(f"  {idx}. {app['name']}")

        category = input("Select category (r=registry, e=exe): ").strip().lower()
        try:
            if category.startswith('r') and registry_apps:
                num = int(input("Enter registry program number: ").strip())
                app_to_analyze = registry_apps[num-1]
            elif category.startswith('e') and exe_apps:
                num = int(input("Enter exe file number: ").strip())
                app_to_analyze = exe_apps[num-1]
            else:
                print("[!] Invalid selection or empty list.")
        except (ValueError, IndexError):
            print("[!] Selection out of range or invalid.")
    else:
        print("[!] No apps available to select.")
    return app_to_analyze


def research_web(app):
    from analysis.web_researcher import search_web_info
    print(f"[*] Researching web for: {app['name']}")
    return search_web_info(app['name'])


def run_llm(web_info):
    from analysis.llm_analyzer import sendToOllama
    return sendToOllama(web_info)


def parse_result(llm_result):
    from analysis.llm_analyzer import parseOllamaRes
    return parseOllamaRes(llm_result)


def main():
    print("[*] Starting AppsAnalyst...")

    # step 0: install and setup LLM (can comment out and assign dummy variable)
    # lm_ready = setup_llm()
    # if not lm_ready:
    #     return

    # step 1: load configuration (not implemented yet)

    # step 2: scan registry and filesystem for apps
    # registry_apps, exe_apps = scan_apps()    
    # Uncomment to skip step 2: 
    # registry_apps, exe_apps = DUMMY_REGISTRY_APPS, DUMMY_EXE_APPS

    # step 3: let user pick an application to analyze
    # app_to_analyze = select_app(registry_apps, exe_apps)  # or: app_to_analyze = registry_apps[0]
    # Uncomment to skip step 3: 
    app_to_analyze = DUMMY_REGISTRY_APPS[0]
    #or all of the dumm apps:
    
    

    if app_to_analyze:
        # step 4: perform web research
        web_info = research_web(app_to_analyze)
        # Uncomment to skip step 4: 
        # web_info = DUMMY_WEB_INFO
        print(f"[v] Web info collected for {app_to_analyze['name']}.")

        # step 5: send to LLM and parse result
        llm_result = run_llm(web_info)           # or: llm_result = DUMMY_LLM_RESPONSE
        if llm_result:
            risk_vector = parse_result(llm_result)   # or: risk_vector = [False, False, False, False]
            print(f"[v] Risk Assessment Vector: {risk_vector}")
        print("[v] LLM analysis completed.")
    else:
        print("[!] No app selected for analysis.")

    print("[v] Scan completed.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        from gui import run_gui
        run_gui()
    else:
        install_missing_requirements()
        main()
