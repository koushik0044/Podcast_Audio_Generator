import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set before any module reads config, so tests never touch a real vendor.
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("SERPER_API_KEY", "test-key")
os.environ.pop("ELEVENLABS_API_KEY", None)
