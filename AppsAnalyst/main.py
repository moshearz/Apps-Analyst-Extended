import sys
import os
import json
import logging
from datetime import datetime
import xml.etree.ElementTree as ET


current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file_path))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from AppsAnalyst.utils.logger import setup_logger
    from AppsAnalyst.collectors.win_apps_scanner import scan_installed_apps
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    print(f"Project Root: {project_root}")
    print(f"Current sys.path: {sys.path[:3]}")
    sys.exit(1)

def generate_xml_report(apps_data, filename="ScanReport.xml"):
   
    root = ET.Element("ScanReport")
    root.set("GeneratedAt", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    for app in apps_data:
        app_node = ET.SubElement(root, "Application")
        ET.SubElement(app_node, "Name").text = str(app.get('Name'))
        ET.SubElement(app_node, "Source").text = str(app.get('Source'))
        ET.SubElement(app_node, "Risk").text = "HIGH" if app.get('IsSuspicious') else "Low"
        
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    return filename

def main():
    logger = setup_logger()
    logger.info("Starting AppsAnalyst Engine...")

 
    logger.info("Scanning for threats (Registry + FileSystem + Memory)...")
    apps_data = scan_installed_apps()
    
    if not apps_data:
        logger.error("No data collected.")
        return

    if isinstance(apps_data, str):
        apps_data = json.loads(apps_data)

    print("\n" + "="*50)
    print(f"{'CURRENT SYSTEM INVENTORY':^50}")
    print("="*50)
    installed = [a for a in apps_data if a.get('Source') == 'Registry']
    for app in sorted(installed, key=lambda x: str(x['Name']))[:100]: # כרגע 100 ררק
        print(f" - {app['Name']}")
    print(f"... and {len(installed)-15} more items.")

    
    print("\n" + "!"*50)
    print(f"{'SECURITY ALERTS':^50}")
    print("!"*50)
    
    suspicious = [a for a in apps_data if a.get('IsSuspicious')]
    if suspicious:
        for app in suspicious:
            logger.warning(f"DETECTION: {app['Name']} found via {app['Source']}!")
            print(f"   >>> RISK: High (Potential Social Engineering Tool)")
    else:
        logger.info("Scan clear. No suspicious tools found.")

 
    report_path = generate_xml_report(apps_data)
    logger.info(f"Report generated: {report_path}")

if __name__ == "__main__":
    main()