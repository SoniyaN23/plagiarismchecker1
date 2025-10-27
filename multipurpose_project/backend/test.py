from googleapiclient.discovery import build


GOOGLE_SEARCH_API_KEY = "YOUR_API_KEY_HERE"
GOOGLE_SEARCH_ENGINE_ID = "YOUR_CSE_ID_HERE"

service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
res = service.cse().list(q="test plagiarism checker text", cx=GOOGLE_SEARCH_ENGINE_ID, num=1).execute()
print(res)
