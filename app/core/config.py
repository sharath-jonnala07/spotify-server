import os
from typing import List
from dotenv import load_dotenv

# Load local environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

class Settings:
    PROJECT_NAME: str = "Spotify Clone API"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174").split(",")
    ]
    
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
