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

import json
from app.models.models import User

@router.get("/", response_model=List[SongResponse])
async def get_recommendations(db: Session = Depends(get_db)):
    cache_key = f"recommendations_{DEFAULT_USER_ID}"
    cached = cache.get(cache_key)
    if cached:
        print("Recommendations cache hit.")
        return cached

    # 1. Load user preferences
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    prefs = {"languages": [], "vibe": "", "artists": []}
    if user and user.preferences:
        try:
            prefs = json.loads(user.preferences)
        except Exception:
            pass

    # 2. Gather seed track IDs (prioritizing likes, then history, then onboarding preferences)
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
                
    # If we need more seeds, look at onboarding favorite artists
    if len(seed_ids) < 3:
        fav_artists = prefs.get("artists", [])
        for artist_name in fav_artists:
            song = db.query(Song).filter(Song.artist.like(f"%{artist_name}%")).first()
            if song:
                s_id = song.spotify_id or (song.id.replace("spotify_", "") if song.id.startswith("spotify_") else None)
                if s_id and s_id not in seed_ids:
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

    # 3. Query Spotify Recommendations API
    results = []
    if seed_ids:
        print(f"Fetching Spotify recommendations using seeds: {seed_ids}")
        results = await spotify_service.get_recommendations(seed_ids)

    # 4. Local Personalization Fallback (if Spotify API returns empty or is unconfigured)
    if not results:
        print("Spotify recommendations empty or unconfigured. Performing local DB personalization.")
        db_songs = db.query(Song).filter(~Song.id.like("pod_%")).all() # Exclude podcasts from music recommendations
        
        scored_songs = []
        preferred_langs = [l.lower() for l in prefs.get("languages", [])]
        user_vibe = prefs.get("vibe", "").lower()
        custom_vibe = prefs.get("custom_vibe", "").lower() if prefs.get("custom_vibe") else ""
        audio_focus = prefs.get("audio_focus", "vibe").lower()
        custom_notes = prefs.get("custom_notes", "").lower() if prefs.get("custom_notes") else ""
        fav_artists = [a.lower() for a in prefs.get("artists", [])]
        
        # Scoring mapping for vibes
        vibe_songs = {
            "focus": ["kabira", "apna bana le", "adiga adiga", "samajavaragamana"],
            "energy": ["naatu naatu", "blinding lights", "shape of you", "stay"],
            "relax": ["flowers", "tum hi ho", "samajavaragamana", "srivalli", "apna bana le"],
            "party": ["naatu naatu", "stay", "blinding lights", "shape of you", "kesariya"],
            "acoustic": ["kabira", "tum hi ho", "flowers", "adiga adiga"],
            "melancholy": ["tum hi ho", "kabira", "adiga adiga"],
            "romance": ["tum hi ho", "kesariya", "apna bana le", "srivalli", "samajavaragamana"],
            "sleep": ["kabira", "adiga adiga", "flowers"]
        }
        
        for s in db_songs:
            score = 0
            
            # A. Language score (+15 if matched)
            song_lang_prefix = s.id.split("_")[0] # e.g. "eng", "hin", "tel", "tam", "kan", "mal"
            if song_lang_prefix == "eng" and "english" in preferred_langs:
                score += 15
            elif song_lang_prefix == "hin" and "hindi" in preferred_langs:
                score += 15
            elif song_lang_prefix == "tel" and "telugu" in preferred_langs:
                score += 15
            elif song_lang_prefix == "tam" and "tamil" in preferred_langs:
                score += 15
            elif song_lang_prefix == "kan" and "kannada" in preferred_langs:
                score += 15
            elif song_lang_prefix == "mal" and "malayalam" in preferred_langs:
                score += 15
            
            # B. Artist score (+20 if matched)
            if any(artist in s.artist.lower() for artist in fav_artists):
                score += 20
                
            # C. Vibe score (+15 if matched)
            if user_vibe in vibe_songs:
                if s.title.lower() in vibe_songs[user_vibe] or any(vibe_song in s.title.lower() for vibe_song in vibe_songs[user_vibe]):
                    score += 15
            elif custom_vibe:
                # Custom vibe matching
                if custom_vibe in s.title.lower() or custom_vibe in s.artist.lower():
                    score += 15

            # D. Audio Focus Score (+15 if matched)
            if audio_focus == "beats":
                # Boost high-tempo, danceable tracks
                if s.title.lower() in ["naatu naatu", "blinding lights", "shape of you", "stay", "samajavaragamana"]:
                    score += 15
            elif audio_focus == "lyrics":
                # Boost storytelling and vocal-centric tracks
                if s.title.lower() in ["tum hi ho", "kabira", "apna bana le", "srivalli", "adiga Adiga"]:
                    score += 15
            elif audio_focus == "ambient":
                # Boost relaxing, instrumental-like focus music
                if s.title.lower() in ["kabira", "apna bana le", "adiga adiga", "flowers"]:
                    score += 15

            # E. Custom notes keyword match (+15 if notes contain relevant terms)
            if custom_notes:
                if "slow" in custom_notes or "sad" in custom_notes or "chill" in custom_notes:
                    if s.title.lower() in ["tum hi ho", "kabira", "adiga adiga", "flowers"]:
                        score += 15
                if "fast" in custom_notes or "dance" in custom_notes or "gym" in custom_notes or "workout" in custom_notes:
                    if s.title.lower() in ["naatu naatu", "blinding lights", "shape of you", "stay"]:
                        score += 15
            
            scored_songs.append((s, score))
            
        # Sort by score descending (high personalization value first)
        scored_songs.sort(key=lambda x: x[1], reverse=True)
        
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
            for s, score in scored_songs
        ]

    # Convert results to schema responses
    responses = [SongResponse(**t) for t in results]
    
    # Cache recommendations for 30 minutes (1800 seconds)
    cache.set(cache_key, responses, 1800)
    return responses

