import requests
import dns.resolver
from shodan import Shodan
import os
import pickle
import time
import logging

def cache_response(key, data, ttl):
    with open(f"data/cache/{key}.pkl", "wb") as f:
        pickle.dump({"data": data, "expiry": time.time() + ttl}, f)

def load_cache(key):
    try:
        with open(f"data/cache/{key}.pkl", "rb") as f:
            cached = pickle.load(f)
            if time.time() < cached["expiry"]:
                return cached["data"]
    except:
        return None

def run(target, profile):
    results = {"osint": {}, "dns": []}
    cache_key = f"shodan_{target}"
    cached = load_cache(cache_key)
    
    if cached:
        results["osint"]["shodan"] = cached
        logging.info(f"Loaded cached Shodan data for {target}")
    else:
        api = Shodan(os.getenv("SHODAN_API_KEY"))
        try:
            host = api.host(target, timeout=profile["timeout"])
            results["osint"]["shodan"] = {
                "os": host.get("os", "unknown"),
                "ports": host.get("ports", []),
                "vulns": host.get("vulns", [])
            }
            cache_response(cache_key, results["osint"]["shodan"], profile["cache_ttl"])
        except Exception as e:
            logging.error(f"Shodan failed for {target}: {e}")
            results["osint"]["shodan"] = {"error": str(e)}

    try:
        whois = requests.get(f"https://api.whois.com/v1/{target}", timeout=profile["timeout"]).json()
        results["osint"]["whois"] = whois
    except Exception as e:
        logging.error(f"WHOIS failed for {target}: {e}")
        results["osint"]["whois"] = {"error": str(e)}

    for qtype in ["A", "MX", "NS", "TXT"]:
        try:
            answers = dns.resolver.resolve(target, qtype)
            results["dns"].append({qtype: [str(a) for a in answers]})
        except Exception as e:
            logging.warning(f"DNS {qtype} lookup failed for {target}: {e}")

    return results
