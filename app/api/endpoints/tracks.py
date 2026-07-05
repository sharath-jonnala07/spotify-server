from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.cache import cache
from app.schemas.schemas import SongResponse, ResolvedTrack
from app.models.models import Song, Like, History, User
from app.services.spotify_service import spotify_service
from app.services.audius_service import audius_service
from app.services.piped_service import piped_service
from app.services.resolver_service import resolver_service
from datetime import datetime

router = APIRouter()

# Default user helper
DEFAULT_USER_ID = "default"

@router.get("/search", response_model=List[SongResponse])
async def search_tracks(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    cache_key = f"search_{q.lower()}"
    cached_results = cache.get(cache_key)
    if cached_results:
        print(f"Search cache hit for: {q}")
        return cached_results

    results = []

    # 1. Search Spotify (Primary Metadata provider)
    results = await spotify_service.search_tracks(q)
    
    # 2. If Spotify returns nothing (or is unconfigured), search Audius
    if not results:
        print("Spotify metadata empty or unconfigured. Searching Audius.")
        results = await audius_service.search_tracks(q)
        
    # 3. If Audius returns nothing, search YouTube
    if not results:
        print("Audius metadata empty. Searching YouTube.")
        results = await piped_service.search_tracks(q)

    # Cache search results for 1 hour (3600 seconds)
    cache.set(cache_key, results, 3600)
    return results

@router.get("/resolve/{track_id}", response_model=ResolvedTrack)
async def resolve_track(track_id: str, db: Session = Depends(get_db)):
    track = await resolver_service.resolve_track(track_id, db)
    if not track:
        raise HTTPException(status_code=404, detail="Track could not be resolved or streamed.")
    return track

@router.post("/history/{track_id}")
async def add_to_history(
    track_id: str, 
    title: str = Query(...), 
    artist: str = Query(...), 
    album: str = Query(...), 
    cover_image: str = Query(""),
    db: Session = Depends(get_db)
):
    # Ensure song metadata exists in DB
    song = db.query(Song).filter(Song.id == track_id).first()
    if not song:
        song = Song(
            id=track_id,
            spotify_id=track_id.replace("spotify_", "") if track_id.startswith("spotify_") else None,
            title=title,
            artist=artist,
            album=album,
            duration="3:30",  # default placeholder
            image_url=cover_image
        )
        db.add(song)
        db.commit()

    # Log in history table
    new_history = History(
        user_id=DEFAULT_USER_ID,
        song_id=track_id,
        played_at=datetime.utcnow()
    )
    db.add(new_history)
    db.commit()
    return {"status": "success", "message": "Track added to history"}

@router.delete("/history/{track_id}")
async def remove_from_history(track_id: str, db: Session = Depends(get_db)):
    db.query(History).filter(History.user_id == DEFAULT_USER_ID, History.song_id == track_id).delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "message": "Track removed from history"}

@router.get("/history", response_model=List[SongResponse])
async def get_history(limit: int = 15, db: Session = Depends(get_db)):
    # Query history join songs
    history_records = (
        db.query(Song)
        .join(History, History.song_id == Song.id)
        .filter(History.user_id == DEFAULT_USER_ID)
        .order_by(History.played_at.desc())
        .limit(limit)
        .all()
    )
    # Filter duplicate tracks from history listing while keeping order
    seen = set()
    unique_history = []
    for song in history_records:
        if song.id not in seen:
            seen.add(song.id)
            unique_history.append(song)
    return unique_history

@router.post("/likes/{track_id}")
async def like_track(
    track_id: str,
    title: str = Query(...),
    artist: str = Query(...),
    album: str = Query(...),
    cover_image: str = Query(""),
    db: Session = Depends(get_db)
):
    # Ensure song metadata exists in DB
    song = db.query(Song).filter(Song.id == track_id).first()
    if not song:
        song = Song(
            id=track_id,
            spotify_id=track_id.replace("spotify_", "") if track_id.startswith("spotify_") else None,
            title=title,
            artist=artist,
            album=album,
            duration="3:30",
            image_url=cover_image
        )
        db.add(song)
        db.commit()

    # Add Like
    existing_like = db.query(Like).filter(Like.user_id == DEFAULT_USER_ID, Like.song_id == track_id).first()
    if not existing_like:
        new_like = Like(
            user_id=DEFAULT_USER_ID,
            song_id=track_id,
            created_at=datetime.utcnow()
        )
        db.add(new_like)
        db.commit()
    return {"status": "success", "message": "Track liked"}

@router.delete("/likes/{track_id}")
async def unlike_track(track_id: str, db: Session = Depends(get_db)):
    like = db.query(Like).filter(Like.user_id == DEFAULT_USER_ID, Like.song_id == track_id).first()
    if like:
        db.delete(like)
        db.commit()
        return {"status": "success", "message": "Track unliked"}
    raise HTTPException(status_code=404, detail="Track like not found")

@router.get("/likes", response_model=List[SongResponse])
async def get_likes(db: Session = Depends(get_db)):
    liked_songs = (
        db.query(Song)
        .join(Like, Like.song_id == Song.id)
        .filter(Like.user_id == DEFAULT_USER_ID)
        .order_by(Like.created_at.desc())
        .all()
    )
    return liked_songs

@router.get("/trending", response_model=List[SongResponse])
async def get_trending_tracks(db: Session = Depends(get_db)):
    cache_key = "trending_tracks_v2"
    cached = cache.get(cache_key)
    if cached:
        print("Trending cache hit.")
        return cached

    # Query database for English, Hindi, and Telugu preloaded songs
    db_songs = db.query(Song).filter(
        Song.id.like("eng_%") | Song.id.like("hin_%") | Song.id.like("tel_%")
    ).all()

    if db_songs:
        responses = [
            SongResponse(
                id=s.id,
                title=s.title,
                artist=s.artist,
                album=s.album,
                duration=s.duration,
                image_url=s.image_url
            )
            for s in db_songs
        ]
        cache.set(cache_key, responses, 3600)
        return responses

    # Fallback to Audius
    results = await audius_service.get_trending_tracks(18)
    responses = [SongResponse(**t) for t in results]
    cache.set(cache_key, responses, 3600)
    return responses

@router.get("/podcasts", response_model=List[SongResponse])
async def get_podcasts(db: Session = Depends(get_db)):
    db_podcasts = db.query(Song).filter(Song.id.like("pod_%")).all()
    return db_podcasts

@router.get("/artists/{artist_name}", response_model=List[SongResponse])
async def get_artist_tracks(artist_name: str):
    cache_key = f"artist_tracks_{artist_name.lower()}"
    cached = cache.get(cache_key)
    if cached:
        print(f"Artist cache hit for: {artist_name}")
        return cached

    results = await spotify_service.search_tracks(artist_name)
    if not results:
        results = await audius_service.search_tracks(artist_name)
        
    responses = [SongResponse(**t) for t in results]
    cache.set(cache_key, responses, 86400)
    return responses

import json
from app.schemas.schemas import UserPreferences

@router.put("/preferences", response_model=Dict[str, Any])
async def update_preferences(prefs: UserPreferences, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(
            id=DEFAULT_USER_ID,
            name="Sharath",
            email="sharath@spotify.local",
            created_at=datetime.utcnow()
        )
        db.add(user)
    
    user.preferences = json.dumps(prefs.model_dump())
    db.commit()
    
    # Invalidate recommendations cache so that they are re-calculated with new preferences
    cache.delete(f"recommendations_{DEFAULT_USER_ID}")
    return {"status": "success", "message": "Preferences updated successfully"}

@router.get("/preferences", response_model=Dict[str, Any])
async def get_preferences(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user or not user.preferences:
        return {"languages": [], "vibe": "", "artists": []}
    
    try:
        return json.loads(user.preferences)
    except Exception:
        return {"languages": [], "vibe": "", "artists": []}

