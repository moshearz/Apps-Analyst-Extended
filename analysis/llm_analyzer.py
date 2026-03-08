def sendToOllama(web_data):
    import ollama
    
# Create the prompt with the specified prefix and web search data
#     prefix = """The following text is a google search result of a single app name. based on the following google search output, Based ONLY on the provided text, determine if the program has the following capabilities built-in: remote access (allowing to traverse the file system, upload and download files executing programs) and/or remote file sharing (like filezilla), and/or keylogging (a process that records in the background every keystroke on the keyboard) and/or server hosting (like a webite the serves some files and may allow to execute some files or upload them). if it is not mentioned in the text, assume it does not have the capability. answer in the following format:
# Remote Administration: [yes/no]
# Remote File Sharing: [yes/no]
# Keylogging: [yes/no]
# Server Hosting: [yes/no]"""
    
#     prompt = f"{prefix}\n\n{web_data}"
    system_instruction = """You are a strict software risk classifier for a security-awareness tool.

You will receive web search text about one software application.

Your task:
1. Summarize what the software does based ONLY on the provided text.
2. Determine whether the software explicitly has each of the following built-in capabilities:
   - Remote Administration
   - Remote File Sharing
   - Keylogging
   - Server Hosting
3. Explain why the software could matter in a social-engineering scenario, especially if a stranger asks the user to download or run it.
4. Provide a clear warning and recommended action for a non-technical user.

Definitions:
- Remote Administration = remote access, remote control, remote desktop, unattended access, remote support, or the ability to control a computer/device remotely.
- Remote File Sharing = file transfer, upload/download, sync, or explicit sending/receiving of files.
- Keylogging = recording keyboard keystrokes in the background.
- Server Hosting = hosting a website, web server, or browser-accessible/network-accessible service.

Rules:
- Base your answer ONLY on the provided text.
- If a capability is NOT explicitly mentioned, answer "no".
- Do NOT use outside knowledge.
- Be conservative and do NOT guess.
- Keep explanations short and direct.
- The first 4 capability lines must appear EXACTLY as written below so they can be parsed by code.

Answer EXACTLY in this structure:

App Overview: [brief summary]

Remote Administration: [yes/no]
Remote File Sharing: [yes/no]
Keylogging: [yes/no]
Server Hosting: [yes/no]

Capability Evidence:
- Remote Administration: [short reason]
- Remote File Sharing: [short reason]
- Keylogging: [short reason]
- Server Hosting: [short reason]

Risk Level: [low/medium/high]

Detected Indicators:
- [indicator 1]
- [indicator 2]
- [indicator 3]

Why This Matters:
[1-3 short sentences explaining what a stranger could potentially do if the user installs or runs this software]

User Warning:
[clear warning for a non-technical user]

Recommended Action:
[clear action such as review, verify source, avoid running, or uninstall if unexpected]
"""
    user_prompt = f"Here is the web search data to analyze:\n\n{web_data}"
    # Send to ollama model gemma3:1b and print the result
    try:
        response = ollama.chat(
            model="gemma3:1b",
            messages=[
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': user_prompt}
            ],
            options={
                "temperature": 0.1 
            }
        )
        result = response['message']['content']
        print(f"\n[Ollama Analysis Result]:\n{result}")
        return result
        
    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None
def parseOllamaRes(ollama_response):
    """
    Parse Ollama response and extract boolean values for risk categories.
    Ignores text between ## markers (explanations).
    Returns a vector of 4 booleans: [Remote Administration, Remote File Sharing, Keylogging, Server Hosting]
    """
    import re
    # Initialize with False values
    result_vector = [False, False, False, False]
    
    # Define the keys to search for (in order)
    keys = ["Remote Administration", "Remote File Sharing", "Keylogging", "Server Hosting"]
    
    # Remove all text between ## markers (explanations) before parsing
    cleaned_response = re.sub(r'##.*?##', '', ollama_response)
    
    # Parse each line to find yes/no values
    for i, key in enumerate(keys):
        for line in cleaned_response.split('\n'):
            if key in line:
                # Extract yes/no value from the line
                if 'yes' in line.lower():
                    result_vector[i] = True
                elif 'no' in line.lower():
                    result_vector[i] = False
                break
    
    return result_vector
