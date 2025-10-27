import os
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import highlight_text_with_explanation
from googleapiclient.discovery import build

GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

def fetch_web_sources(text):
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        print("WARNING: Google Search API keys missing. Using mock data.")
        return [{
            "url": "https://mock.plagiarism.check/missing-key",
            "content": "This is a sample text from article one.",
            "excerpt": "API keys missing. Showing mock data."
        }]
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        search_query = text[:100].strip() or "plagiarism checker test"
        res = service.cse().list(q=search_query, cx=GOOGLE_SEARCH_ENGINE_ID, num=5).execute()

        live_sources = []
        if 'items' in res:
            for item in res['items']:
                live_sources.append({
                    "url": item.get('link', 'N/A'),
                    "content": item.get('snippet', ''),
                    "excerpt": item.get('snippet', '')[:80] + "..."
                })
        return live_sources
    except Exception as e:
        print(f"Google Search API Error: {e}")
        return [{
            "url": "https://api.error.plagiarism.check",
            "content": "API call failed.",
            "excerpt": f"Search Error: {e}"
        }]

def cosine_similarity_score(text1, text2):
    """Compute cosine similarity between two texts using TF-IDF"""
    vectorizer = TfidfVectorizer().fit([text1, text2])
    tfidf_matrix = vectorizer.transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return similarity

def check_plagiarism(text, method="cosine"):
    """
    method="cosine"  -> Use TF-IDF + Cosine Similarity
    method="sequence" -> Use SequenceMatcher
    """
    live_sources = fetch_web_sources(text)
    explanation = []
    highlighted_segments_data = []
    similarity_score = 0

   
    chunks = [chunk.strip() for chunk in text.replace("\n", " ").split(".") if chunk.strip()]

    for source in live_sources:
        source_content = source.get("content", "")
        if not source_content:
            continue

        for chunk in chunks:
            if method == "cosine":
                ratio = cosine_similarity_score(chunk.lower(), source_content.lower())
            else:  
                ratio = SequenceMatcher(None, chunk.lower(), source_content.lower()).ratio()

            if ratio > 0.2: 
                highlighted_segments_data.append(source)
                similarity_score = max(similarity_score, int(ratio * 100))

                if ratio > 0.8:
                    explanation.append(f"Exact or very close meaning ({int(ratio*100)}%) detected from {source['url']}")
                elif ratio > 0.5:
                    explanation.append(f"High similarity/Paraphrased content ({int(ratio*100)}%) detected from {source['url']}")
                else:
                    explanation.append(f"Possible common phrase ({int(ratio*100)}%) detected from {source['url']}")

    if not explanation:
        explanation.append("Your text appears original! Remember to cite your sources properly.")
    else:
        explanation.append("💡 Suggestion: Use the 'Suggest Paraphrase' feature for flagged sentences to improve originality.")
        explanation.append("💡 Suggestion: Always cite the source for any matched content found.")

    highlighted_text = highlight_text_with_explanation(text, highlighted_segments_data)

    
    formatted_sources = []
    unique_urls = set()
    for s in highlighted_segments_data:
        if s["url"] not in unique_urls:
            formatted_sources.append({"url": s["url"], "excerpt": s["excerpt"]})
            unique_urls.add(s["url"])

    return {
        "similarity": similarity_score,
        "highlighted_text": highlighted_text,
        "sources": formatted_sources,
        "explanation": explanation
    }
