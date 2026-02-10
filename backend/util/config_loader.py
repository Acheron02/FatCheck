# backend/util/config_loader.py
import json
import os

def load_config():
    # Adjust path to point to config folder in root
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    config_path = os.path.join(root_dir, "config", "config.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, "r") as f:
        config = json.load(f)
    return config
