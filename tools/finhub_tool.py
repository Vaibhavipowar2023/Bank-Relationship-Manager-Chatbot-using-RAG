# tools/finnhub_tool.py
import requests, os
def get_repo_rate():
    token = os.getenv("FINNHUB_API_KEY")
    url = f"https://finnhub.io/api/v1/economic-data?symbol=INREPO&token={token}"
    r = requests.get(url)
    data = r.json()
    val = data.get("data")[-1]["value"] if data.get("data") else "unknown"
    return f"India’s current repo rate is about {val}% according to Finnhub."
