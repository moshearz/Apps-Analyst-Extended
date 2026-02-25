def sendToOllama(web_data):
    import ollama
    
    # Create the prompt with the specified prefix and web search data
    prefix = """The following text is a google search result of a single app name. based on the following google search output, does this program allow remote administration (as in remote desktop) and/or remote file sharing (like filezilla), and/or keylogging and/or server hosting?
answer in the following format:
Remote Administration: [yes/no]
Remote File Sharing: [yes/no]
Keylogging: [yes/no]
Server Hosting: [yes/no]"""
    
    prompt = f"{prefix}\n\n{web_data}"
    
    # Send to ollama model gemma3:1b and print the result
    try:
        response = ollama.generate(model="gemma3:1b", prompt=prompt, stream=False)
        result = response['response']
        print(f"\n[Ollama Analysis Result]:\n{result}")
        return result
    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None
def parseOllamaRes(ollama_response):
    """
    Parse Ollama response and extract boolean values for risk categories.
    Returns a vector of 4 booleans: [Remote Administration, Remote File Sharing, Keylogging, Server Hosting]
    """
    # Initialize with False values
    result_vector = [False, False, False, False]
    
    # Define the keys to search for (in order)
    keys = ["Remote Administration", "Remote File Sharing", "Keylogging", "Server Hosting"]
    
    # Parse each line to find yes/no values
    for i, key in enumerate(keys):
        for line in ollama_response.split('\n'):
            if key in line:
                # Extract yes/no value from the line
                if 'yes' in line.lower():
                    result_vector[i] = True
                elif 'no' in line.lower():
                    result_vector[i] = False
                break
    
    return result_vector
