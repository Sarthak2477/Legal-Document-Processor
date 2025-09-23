#!/usr/bin/env python3
import subprocess
import sys

def ensure_spacy_model():
    """Download spaCy model if not already present"""
    try:
        import spacy
        spacy.load("en_core_web_sm")
        print("spaCy model already available")
    except OSError:
        print("Downloading spaCy model...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("spaCy model downloaded successfully")

if __name__ == "__main__":
    ensure_spacy_model()
    # Start the main application
    import subprocess
    subprocess.run([sys.executable, "run_api.py"])
