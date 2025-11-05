# tools/web_search_tool.py
from duckduckgo_search import DDGS

def web_search(query, max_results=3):
    """Search DuckDuckGo for a query and return summarized results."""
    try:
        results = DDGS().text(query, max_results=max_results)
        summaries = []
        for res in results:
            title = res.get("title", "")
            snippet = res.get("body", "")
            url = res.get("href", "")
            summaries.append(f"{title}\n{snippet}\nURL: {url}")
        return "\n\n".join(summaries)
    except Exception as e:
        return f"Web search failed: {str(e)}"
