import re

def highlight_text_with_explanation(text, sources):
    """
    Highlight plagiarized segments with colors:
    - Red: Exact match
    - Orange: Paraphrased
    - Yellow: Common phrase
    """
    highlighted = text
    for source in sources:
        for word in source["content"].split():
            if word in text:
                highlighted = re.sub(
                    f"\\b{re.escape(word)}\\b",
                    f"<mark style='background-color:orange'>{word}</mark>",
                    highlighted,
                    flags=re.IGNORECASE
                )
    return highlighted
