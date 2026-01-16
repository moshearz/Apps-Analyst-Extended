import logging
from utils.logger import setup_logger
from config import load_config

def main():
    logger = setup_logger()
    logger.info("Starting AppsAnalyst...")
    # 0. Install and Setup LLM
    from utils.llm_setup import check_and_pull_model
    if not check_and_pull_model("ministral-3:3b"):
        logger.error("LLM model setup failed. Exiting.")
        return
    logger.info("LLM model is ready.")
    
    # 1. Load Config
    # 2. Run Collectors
    # 3. Run Analysis
    # 4. Generate Report

    logger.info("Scan completed.")

if __name__ == "__main__":
    main()
