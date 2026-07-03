import os
from typing import List

class Settings:
    PROJECT_NAME: str = "Spotify Clone API"
    
    # SQLite Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./spotify.db")
    
    # Spotify API (Optional - falls back to Audius/YouTube search if empty)
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    # Piped YouTube Instances (with auto-rotation)
    PIPED_INSTANCES: List[str] = [
        "https://pipedapi.kavin.rocks",
        "https://piped-api.lunar.icu",
        "https://pipedapi.colt.rest",
        "https://api.piped.yt",
        "https://pipedapi.ox.rs"
    ]
    
    # Audius Nodes
    AUDIUS_BASE_URL: str = "https://api.audius.co"

settings = Settings()
