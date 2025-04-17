# utils.py
import os
from pathlib import Path
import json

def setup_gdrive_auth():
    """
    Guide users through the setup process for Google Drive authentication.
    """
    credentials_path = Path("credentials.json")
    
    if not credentials_path.exists():
        print("\n=== Google Drive Authentication Setup ===")
        print("""
