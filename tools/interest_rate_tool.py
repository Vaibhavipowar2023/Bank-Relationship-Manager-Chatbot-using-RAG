# tools/interest_rate_tool.py
import requests, re

def get_interest_rates():
    results = {}
    try:
        r = requests.get("https://www.idfcfirstbank.com/personal-banking/accounts/savings-account/interest-rate", timeout=8)
        rates = re.findall(r"(\d+\.\d+%)", r.text)
        if rates:
            results["IDFC FIRST Bank"] = f"{rates[0]} to {rates[-1]}"
    except Exception:
        pass
    try:
        r = requests.get("https://www.hdfcbank.com/personal/save/accounts/savings-accounts/savings-account-interest-rate", timeout=8)
        m = re.search(r"(\d+\.\d+%)", r.text)
        if m:
            results["HDFC Bank"] = m.group(1)
    except Exception:
        pass
    try:
        r = requests.get("https://www.icicibank.com/personal-banking/accounts/savings-account/interest-rates", timeout=8)
        m = re.search(r"(\d+\.\d+%)", r.text)
        if m:
            results["ICICI Bank"] = m.group(1)
    except Exception:
        pass

    if not results:
        return "I'm unable to fetch live rates right now."

    # Convert to a readable sentence
    parts = [f"{bank} offers around {rate}" for bank, rate in results.items()]
    sentence = "; ".join(parts) + "."
    return f"Based on the latest public data, {sentence}"
