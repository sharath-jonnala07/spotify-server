from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.cache import cache
from app.schemas.schemas import SongResponse
from app.models.models import Like, History, Song
from app.services.spotify_service import spotify_service

router = APIRouter()
DEFAULT_USER_ID = "default"

@router.get("/", response_model=List[SongResponse])
async def get_recommendations(db: Session = Depends(get_db)):
    cache_key = f"recommendations_{DEFAULT_USER_ID}"
    cached = cache.get(cache_key)
    if cached:
        print("Recommendations cache hit.")
        return cached

    # 1. Gather seed track IDs (from likes first, then history)
    likes = (
        db.query(Like)
        .filter(Like.user_id == DEFAULT_USER_ID)
        .order_by(Like.created_at.desc())
        .limit(3)
        .all()
    )
    seed_ids = []
    for l in likes:
        song = db.query(Song).filter(Song.id == l.song_id).first()
        if song:
            s_id = song.spotify_id or (song.id.replace("spotify_", "") if song.id.startswith("spotify_") else None)
            if s_id:
                seed_ids.append(s_id)
                
    if len(seed_ids) < 3:
        history = (
            db.query(History)
            .filter(History.user_id == DEFAULT_USER_ID)
            .order_by(History.played_at.desc())
            .limit(3)
            .all()
        )
        for h in history:
            song = db.query(Song).filter(Song.id == h.song_id).first()
            if song:
                s_id = song.spotify_id or (song.id.replace("spotify_", "") if song.id.startswith("spotify_") else None)
                if s_id and s_id not in seed_ids:
                    seed_ids.append(s_id)

    # 2. Query Spotify Recommendations API
    results = []
    if seed_ids:
        print(f"Fetching Spotify recommendations using seeds: {seed_ids}")
        results = await spotify_service.get_recommendations(seed_ids)

    # 3. Fallback: Return all preloaded catalog tracks in the SQLite database
    if not results:
        print("Spotify recommendations empty or unconfigured. Falling back to DB tracks.")
        db_songs = db.query(Song).all()
        results = [
            {
                "id": s.id,
                "spotify_id": s.spotify_id,
                "title": s.title,
                "artist": s.artist,
                "album": s.album,
                "duration": s.duration,
                "image_url": s.image_url
            }
            for s in db_songs
        ]

    # Convert results to schema responses
    responses = [SongResponse(**t) for t in results]
    
    # Cache recommendations for 30 minutes (1800 seconds)
    cache.set(cache_key, responses, 1800)
    return responses
