from ddgs import DDGS

def search_web_info(app_name):
    query = f"what is {app_name} software overview"
    print(f"Searching for: {query}\n")
    
    with DDGS() as ddgs:
        # שליפת התוצאות הראשונות
        results = ddgs.text(query, max_results=10, backend="duckduckgo", region='us-en')
        
        extracted_info = ""
        for r in results:
            extracted_info += f"- Title: {r['title']}\n"
            extracted_info += f"  Info: {r['body']}\n\n"
        print(f"Extracted Web Info:\n{extracted_info}")
        return extracted_info

# בדיקה
# info = search_web_info("TeamViewer")
# print(info)