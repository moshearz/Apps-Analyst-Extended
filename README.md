# Apps-analyst - Project Overview
This project is meant to solve the problem of people being uninformed about the programs that are installed on their computer or extentions on their browser. By creating awareness we hope to help fortify the cybernetic space against common cyber crimes.

## How to use Apps-analyst | Quick Start Guide
1. Clone the repository to your local machine. 


# The Detection Challenge: Registry vs. FileSystem
During development, we identified a critical security gap in how Windows manages software visibility:

The Registry Layer (Inventory): Most security tools check the Windows Registry for installed applications. However, attackers often use Portable versions of tools to avoid leaving traces in the official "Add/Remove Programs" list.

The FileSystem Layer (Threat Hunting): Our tool performs active "Threat Hunting" by scanning the FileSystem (Downloads, Desktop) for .exe files.

The Case of AnyDesk: Programs like AnyDesk or TeamViewer are frequently used by attackers in their portable form. By cross-referencing the Registry with the FileSystem and active Memory Processes, Apps-analyst can detect these tools even if they were never "installed" on the machine.

# Social Engineering & Contextual Awareness
Social Engineering is the psychological manipulation of people into performing actions or divulging confidential information.

Our Use Case: The Tech Support Scam
In a typical scenario, an attacker calls a victim pretending to be "Microsoft Support" and convinces them to download a remote access tool (like AnyDesk) to "fix a virus." Because the user downloads and runs the file manually:

The tool is not registered in the System Registry.

Standard antivirus might not flag it as it is a "legitimate" tool.

Apps-analyst identifies this anomaly by flagging high-risk tools found in the Downloads folder or running in memory without an official installation record, providing a critical warning against ongoing Social Engineering attacks.

# Technical Implementation
Language: Python 3.12 (Logic & Analysis).

Collector: PowerShell (Low-level system data retrieval).

Detection Vectors: * Registry Keys: For official software inventory.

Active Processes: For real-time detection of running tools.

Heuristic File Scan: For detecting portable artifacts in user directories.

Reporting: Generates a structured XML report for audit and forensic analysis.