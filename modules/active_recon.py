import nmap
from bs4 import BeautifulSoup
import requests
import logging

def run(target, profile):
    results = {"ports": [], "web": {}}
    
    nm = nmap.PortScanner()
    try:
        nm.scan(target, "22-443", arguments=f"-T{profile['timeout']}")
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                ports = nm[host][proto].keys()
                results["ports"].extend(ports)
    except Exception as e:
        logging.error(f"Nmap scan failed for {target}: {e}")

    try:
        resp = requests.get(f"http://{target}", timeout=profile["timeout"])
        soup = BeautifulSoup(resp.text, "html.parser")
        results["web"]["links"] = [a["href"] for a in soup.find_all("a", href=True)]
        results["web"]["title"] = soup.title.string if soup.title else "No title"
    except Exception as e:
        logging.error(f"Web crawl failed for {target}: {e}")
        results["web"]["error"] = str(e)

    return results
