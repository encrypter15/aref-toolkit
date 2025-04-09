import pytest
from modules import passive_recon

def test_shodan_failure(monkeypatch):
    def mock_shodan(*args, **kwargs):
        raise Exception("API error")
    monkeypatch.setattr("shodan.Shodan.host", mock_shodan)
    profile = {"timeout": 5, "cache_ttl": 3600}
    result = passive_recon.run("example.com", profile)
    assert "error" in result["osint"]["shodan"]
