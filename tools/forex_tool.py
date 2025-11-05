# tools/forex_tool.py
import requests

def get_fx_rate(base="USD", target="INR"):
    try:
        r = requests.get(f"https://api.exchangerate.host/convert?from={base}&to={target}")
        data = r.json()
        return {"status": "ok", "rate": data.get("result"), "info": data.get("info")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
