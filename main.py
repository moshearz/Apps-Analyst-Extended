# from config import load_config

def main():
    print("[*] Starting AppsAnalyst...")
    # 0. Install and Setup LLM
    # from utils.llm_setup import check_and_pull_model
    # if not check_and_pull_model("gemma3:1b"):
    #     print("[!] LLM model setup failed. Exiting.")
    #     return
    # print("[v] LLM model is ready.")
    
    # 1. Load Config

    # 2. Run file and registry scanners
    # from collectors.win_apps_scanner import WinAppsScanner
    # scanner = WinAppsScanner()
    # apps = scanner.scan_apps()
    # print(f"[*] Found {len(apps)} apps.")

    # 3. show user and ask which app to analyze
    #for testing apps only contains the app name "teamviewer":
    apps = [{"name": "TeamViewer"}]
    
    # 4. Run web researcher
    from analysis.web_researcher import search_web_info
    app_to_analyze = apps[0] if apps else None
    if app_to_analyze:
        print(f"[*] Analyzing app: {app_to_analyze['name']}")
        web_info = search_web_info(app_to_analyze['name'])
        print(f"[v] Web info collected for {app_to_analyze['name']}.")
        # 5. Run LLM analysis
        from analysis.llm_analyzer import sendToOllama, parseOllamaRes
        llm_result = sendToOllama(web_info)
        if llm_result:
            risk_vector = parseOllamaRes(llm_result)
            print(f"[v] Risk Assessment Vector: {risk_vector}")
        print("[v] LLM analysis completed.")
    else:
        print("[!] No apps found to analyze.")

    print("[v] Scan completed.")

if __name__ == "__main__":
    main()
