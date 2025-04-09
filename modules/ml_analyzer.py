import torch
from transformers import BertTokenizer, BertModel
import pandas as pd
import requests
import json
from sklearn.preprocessing import StandardScaler
from bs4 import BeautifulSoup
import logging

class VulnerabilityPredictor:
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = BertModel.from_pretrained("bert-base-uncased")
        try:
            self.model.load_state_dict(torch.load("data/model.pth"))
            logging.info("Loaded pretrained model from data/model.pth")
        except:
            logging.warning("No pretrained model found at data/model.pth")
        self.scaler = StandardScaler()

    def fetch_threat_intel(self, feeds):
        intel = {}
        if "cve" in feeds:
            try:
                resp = requests.get("https://cve.circl.lu/api/last", timeout=5).json()
                intel["cve"] = [cve["id"] for cve in resp[:10]]
            except Exception as e:
                logging.error(f"CVE feed failed: {e}")
        if "exploitdb" in feeds:
            try:
                resp = requests.get("https://www.exploit-db.com/rss.xml", timeout=5)
                soup = BeautifulSoup(resp.content, "xml")
                intel["exploitdb"] = [item.find("title").text for item in soup.find_all("item")][:5]
            except Exception as e:
                logging.error(f"ExploitDB feed failed: {e}")
        return intel

    def extract_features(self, passive_data):
        features = {}
        if "shodan" in passive_data["osint"]:
            shodan = passive_data["osint"]["shodan"]
            os = shodan.get("os", "unknown")
            ports = shodan.get("ports", [])
            vulns = shodan.get("vulns", [])
            text = f"OS: {os}, Ports: {', '.join(map(str, ports))}, Vulns: {', '.join(vulns)}"
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)
            features["embedding"] = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            features["port_count"] = len(ports)
            features["vuln_count"] = len(vulns)
        return features

    def predict(self, features):
        if not features:
            return {"error": "No features extracted"}
        X  X = pd.DataFrame([[
            features["port_count"],
            features["vuln_count"]
        ]], columns=["ports", "vulns"])
        X_scaled = self.scaler.fit_transform(X)
        score = min(0.9, max(0.1, X_scaled[0][0] * 0.3 + X_scaled[0][1] * 0.7))
        return {"vulnerability_score": float(score)}

def analyze(passive_data, profile):
    predictor = VulnerabilityPredictor()
    intel = predictor.fetch_threat_intel(profile["ml_feeds"])
    features = predictor.extract_features(passive_data)
    prediction = predictor.predict(features)
    return {
        "threat_intel": intel,
        "features": {k: v.tolist() if hasattr(v, "tolist") else v for k, v in features.items()},
        "prediction": prediction
    }
