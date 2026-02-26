def sendToOllama(web_data):
    import ollama
    
# Create the prompt with the specified prefix and web search data
#     prefix = """The following text is a google search result of a single app name. based on the following google search output, Based ONLY on the provided text, determine if the program has the following capabilities built-in: remote access (allowing to traverse the file system, upload and download files executing programs) and/or remote file sharing (like filezilla), and/or keylogging (a process that records in the background every keystroke on the keyboard) and/or server hosting (like a webite the serves some files and may allow to execute some files or upload them). if it is not mentioned in the text, assume it does not have the capability. answer in the following format:
# Remote Administration: [yes/no]
# Remote File Sharing: [yes/no]
# Keylogging: [yes/no]
# Server Hosting: [yes/no]"""
    
#     prompt = f"{prefix}\n\n{web_data}"
    system_instruction = """ Analyze the provided web search text explain to yourself what the application does and how it does it. finally determine if the software has the following capabilities built-in:
1. Remote Administration (might be described as one of the following: remote access or remote control or remote desktop or similar terms indicating the ability to control the software or a system remotely)
2. Remote File Sharing (file transfer or uploading/downloading files)
3. Keylogging (a process that records in the background every keystroke on the keyboard)
4. Server Hosting (a webite that is accesible via browser)

RULES:
- Base your answer ONLY on the provided text.
- If a capability is NOT explicitly mentioned, you MUST assume it does not have it and answer 'no'.
- You MUST provide a brief explanation for each decision wrapped in double-hash marks like: ## Explanation: reason ##
- Answer EXACTLY in this format:
app overview: [a brief summary of what the software does based on the provided text]
Remote Administration: [yes/no] ## Explanation: your reason ##
Remote File Sharing: [yes/no] ## Explanation: your reason ##
Keylogging: [yes/no] ## Explanation: your reason ##
Server Hosting: [yes/no] ## Explanation: your reason ##"""

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
                "temperature": 0.0 # קריטי למודלים קטנים: מונע מהם "להמציא" תשובות
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
