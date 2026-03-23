# Apps-Analyst 🔍

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/Platform-Windows-blue.svg)](https://www.microsoft.com/windows)

**AI-Powered Security Awareness Tool for Windows Applications**

Apps-Analyst is an innovative security awareness tool that helps users identify potentially risky applications on their Windows computers. Using advanced AI analysis and comprehensive system scanning, it provides detailed risk assessments to protect against social engineering attacks and unauthorized software installations.

---

## 🚀 Key Features

### 🔍 **Comprehensive System Scanning**

- **Registry Analysis**: Scans Windows Registry for officially installed programs
- **Filesystem Monitoring**: Detects portable executables in user directories
- **Real-time Detection**: Identifies running processes and unauthorized installations

### 🤖 **AI-Powered Risk Assessment**

- **Local LLM Analysis**: Uses Ollama with Gemma 3.1B for privacy-focused analysis
- **Multi-dimensional Risk Evaluation**: Assesses 4 critical security categories
- **Contextual Intelligence**: Understands social engineering attack patterns

### 📊 **Professional Reporting**

- **Detailed PDF Reports**: Comprehensive security analysis with recommendations
- **CSV Export**: Spreadsheet-compatible data for further analysis
- **Interactive GUI**: User-friendly interface for non-technical users

### 🛡️ **Security Focus Areas**

- **Remote Administration Tools**: TeamViewer, AnyDesk, VNC detection
- **File Sharing Applications**: Unauthorized upload/download capabilities
- **Keylogging Software**: Keystroke recording detection
- **Server Hosting Tools**: Web server and hosting service identification

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Risk Assessment](#risk-assessment)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Ollama**: [Install Ollama](https://ollama.ai/download)
- **Windows OS**: Windows 10/11 (64-bit)

### Step-by-Step Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/apps-analyst.git
   cd apps-analyst
   ```

2. **Install Ollama and Model**

   ```bash
   # Install Ollama (if not already installed)
   # Download and run the installer from https://ollama.ai/download

   # Pull the required model
   ollama pull gemma3:1b
   ```

3. **Install Python Dependencies**

   ```bash
   python -m pip install --user --force-reinstall -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python main.py --help
   ```

---

## 🚀 Quick Start

### GUI Mode (Recommended)

```bash
python main.py --gui
```

### Command Line Mode

```bash
python main.py
```

### First Run

1. Launch the application
2. Click "Scan System" to discover installed applications
3. Select an application to analyze
4. Review the AI-generated risk assessment
5. Export results as PDF or CSV

---

## 📖 Usage

### GUI Interface

1. **System Scan**: Click "Scan System" to discover applications
2. **Application Selection**: Choose from Registry apps or detected executables
3. **AI Analysis**: Wait for web research and LLM analysis
4. **Review Results**: Examine risk assessment and recommendations
5. **Export Reports**: Generate PDF or CSV reports

### Command Line Interface

```bash
# Start GUI
python main.py --gui

# Start CLI (follow interactive prompts)
python main.py
```

### Advanced Options

- **Custom Model**: Modify `llm_analyzer.py` to use different Ollama models
- **Scan Depth**: Adjust scanning parameters in `config.yaml`
- **Export Formats**: PDF and CSV reports with detailed analysis

---

## 🏗️ Architecture

```
Apps-Analyst/
├── collectors/           # System scanning modules
│   ├── win_apps_scanner.py    # Registry & filesystem scanning
│   └── chrome_ext_scanner.py  # Browser extension analysis
├── analysis/             # AI analysis components
│   ├── llm_analyzer.py        # Ollama LLM integration
│   └── web_researcher.py      # DuckDuckGo web research
├── utils/                # Utility functions
│   ├── llm_setup.py           # Model management
│   └── config management
├── gui.py                # Graphical user interface
├── main.py               # CLI entry point
└── requirements.txt      # Python dependencies
```

### Data Flow

1. **Collection**: Registry + Filesystem scanning
2. **Research**: Web search for application information
3. **Analysis**: LLM processing and risk assessment
4. **Reporting**: PDF/CSV generation with recommendations

---

## 🎯 Risk Assessment

### Risk Categories

| Category                  | Description                                | Risk Level |
| ------------------------- | ------------------------------------------ | ---------- |
| **Remote Administration** | Remote desktop, VNC, TeamViewer-like tools | 🔴 High    |
| **Remote File Sharing**   | File transfer, sync, sharing applications  | 🟡 Medium  |
| **Keylogging**            | Keystroke recording, monitoring software   | 🔴 High    |
| **Server Hosting**        | Web servers, hosting services              | 🟡 Medium  |

### Risk Levels

- **🔴 HIGH**: Immediate action required - potential security threat
- **🟡 MEDIUM**: Review recommended - may be legitimate business tool
- **🟢 LOW**: Generally safe - common legitimate software

### Social Engineering Context

The tool specifically addresses:

- **Tech Support Scams**: Fake Microsoft support calling users
- **Malware Distribution**: Trojans disguised as legitimate tools
- **Unauthorized Access**: Remote control without user consent

---

## 📋 Requirements

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for web research

### Python Dependencies

```
requests>=2.25.0
pyyaml>=5.4.0
beautifulsoup4>=4.9.0
wmi>=1.5.0
ollama>=0.1.0
ddgs>=0.1.0
tqdm>=4.50.0
reportlab>=3.6.0
setuptools>=50.0.0
```

### External Dependencies

- **Ollama**: Local LLM runtime
- **Gemma 3.1B**: AI model for analysis

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Commit** your changes: `git commit -am 'Add feature'`
4. **Push** to the branch: `git push origin feature-name`
5. **Submit** a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure Windows compatibility

### Reporting Issues

- Use GitHub Issues for bug reports
- Include system information and error logs
- Provide steps to reproduce the issue

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Disclaimer**: This tool is designed for security awareness and educational purposes. It is NOT a replacement for professional antivirus software or security solutions.

### Support

- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Comprehensive guides in `/docs`
- **Community**: Join discussions in GitHub Discussions

---

## 🙏 Acknowledgments

- **Ollama** for providing local LLM capabilities
- **DuckDuckGo** for privacy-focused search API
- **ReportLab** for PDF generation
- **Python Community** for excellent libraries

---

**🔒 Stay Secure**: Regular security awareness is your best defense against cyber threats.

---

_Last updated: March 2026_
