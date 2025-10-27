from difflib import SequenceMatcher
import re

def preprocess_code(code):
    
    code = re.sub(r'#.*', '', code)  
    code = re.sub(r'\s+', ' ', code)
    return code.strip()

def check_code(code_text):
    
    DUMMY_CODE_DB = [
        "def add(a, b): return a + b",
        "for i in range(10): print(i)"
    ]

    code_text_clean = preprocess_code(code_text)
    similarity_score = 0
    highlighted_code = code_text

    for snippet in DUMMY_CODE_DB:
        snippet_clean = preprocess_code(snippet)
        ratio = SequenceMatcher(None, code_text_clean, snippet_clean).ratio()
        if ratio > 0.3:
            similarity_score = max(similarity_score, int(ratio * 100))
            highlighted_code = highlighted_code.replace(snippet.split()[0], f"<mark>{snippet.split()[0]}</mark>")

    return {
        "similarity": similarity_score,
        "highlighted_code": highlighted_code
    }
