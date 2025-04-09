#!/usr/bin/env python3
import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def generate_key(passphrase):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"salt_", iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return Fernet(key)

def encrypt_file(passphrase):
    with open("config/credentials.json", "rb") as f:
        data = f.read()
    fernet = generate_key(passphrase)
    encrypted = fernet.encrypt(data)
    with open("config/credentials.enc", "wb") as f:
        f.write(encrypted)
    print("[+] Credentials encrypted to config/credentials.enc")

def decrypt_file(passphrase):
    with open("config/credentials.enc", "rb") as f:
        data = f.read()
    fernet = generate_key(passphrase)
    decrypted = fernet.decrypt(data)
    return json.loads(decrypted)

if __name__ == "__main__":
    passphrase = os.getenv("CREDS_PASSPHRASE")
    if not passphrase:
        print("[-] Set CREDS_PASSPHRASE env var.")
        exit(1)
    encrypt_file(passphrase)
