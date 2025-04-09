#!/usr/bin/env python3
import torch
from transformers import BertTokenizer, BertModel
import requests
import json
import logging

logging.basicConfig(filename="logs/aref.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_training_data():
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?resultsPerPage=50"
    try:
        resp = requests.get(url, timeout=10).json()
        data = []
        for cve in resp["vulnerabilities"]:
            cve_id = cve["cve"]["id"]
            desc = cve["cve"]["descriptions"][0]["value"]
            # Label: 1 if CVSS score >= 7 (critical/high), 0 otherwise
            score = cve["cve"]["metrics"].get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseScore", 0)
            label = 1 if score >= 7 else 0
            # Simulate OS and ports (real data would come from Shodan in prod)
            text = f"OS: Unknown, Vulns: {cve_id}, Desc: {desc}"
            data.append({"text": text, "label": label})
        logging.info(f"Fetched {len(data)} CVEs from NVD")
        return data
    except Exception as e:
        logging.error(f"NVD fetch failed: {e}")
        return []

def train():
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    model = BertModel.from_pretrained("bert-base-uncased")
    data = fetch_training_data()
    
    if not data:
        print("[-] No training data fetched. Exiting.")
        exit(1)
    
    inputs = tokenizer([d["text"] for d in data], return_tensors="pt", padding=True, truncation=True, max_length=128)
    labels = torch.tensor([d["label"] for d in data], dtype=torch.float32)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)
    model.train()
    for epoch in range(3):  # Fewer epochs for efficiency, adjust in prod
        outputs = model(**inputs)
        loss = torch.nn.MSELoss()(outputs.last_hidden_state.mean(dim=1).squeeze(), labels)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        logging.info(f"Epoch {epoch+1}, Loss: {loss.item()}")
    
    torch.save(model.state_dict(), "data/model.pth")
    print("[+] Model trained and saved to data/model.pth")

if __name__ == "__main__":
    train()
