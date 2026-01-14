import logging
from utils.logger import setup_logger
from config import load_config

def main():
    logger = setup_logger()
    logger.info("Starting AppsAnalyst...")

    # 1. Load Config
    # 2. Run Collectors
    # 3. Run Analysis
    # 4. Generate Report

    logger.info("Scan completed.")

if __name__ == "__main__":
    main()
