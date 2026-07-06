from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.core.database import get_db
from app.core.cache import cache
from app.schemas.schemas import SongResponse, RecommendationFeedResponse
from app.models.models import Like, History, Song, User
from app.services.groq_service import groq_service

router = APIRouter()
DEFAULT_USER_ID = "default"

@router.get("/", response_model=RecommendationFeedResponse)
async def get_recommendations(
    local_time: Optional[str] = Query(None),
    local_day: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # 1. Load user preferences
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    prefs = {"languages": [], "vibe": "", "artists": [], "discovery_appetite": 50, "exploration_depth_width": 50, "stories": []}
    if user and user.preferences:
        try:
            prefs = json.loads(user.preferences)
        except Exception:
            pass

    # Determine active stories to compute unique cache key
    active_stories = [s for s in prefs.get("stories", []) if groq_service.is_story_active(s, local_time, local_day)]
    active_stories_str = ",".join([s.get("id") for s in active_stories])
    
    cache_key = f"recommendations_{DEFAULT_USER_ID}_{prefs.get('discovery_appetite')}_{prefs.get('exploration_depth_width')}_{active_stories_str}"
    
    cached = cache.get(cache_key)
    if cached:
        print("Recommendations cache hit.")
        # Ensure we return a RecommendationFeedResponse-compatible type
        return cached

    # 2. Get all songs from DB to select from
    db_songs = db.query(Song).filter(~Song.id.like("pod_%")).all()
    song_database_dicts = [
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

    # Gather liked songs
    likes = (
        db.query(Like)
        .filter(Like.user_id == DEFAULT_USER_ID)
        .all()
    )
    liked_songs_dicts = []
    for l in likes:
        song = db.query(Song).filter(Song.id == l.song_id).first()
        if song:
            liked_songs_dicts.append({
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album
            })

    # Gather history
    history = (
        db.query(History)
        .filter(History.user_id == DEFAULT_USER_ID)
        .order_by(History.played_at.desc())
        .limit(10)
        .all()
    )
    history_songs_dicts = []
    for h in history:
        song = db.query(Song).filter(Song.id == h.song_id).first()
        if song:
            history_songs_dicts.append({
                "id": song.id,
                "title": song.title,
                "artist": song.artist,
                "album": song.album
            })

    # 3. Call groq_service to orchestrate AI recommendations
    personalization_result = await groq_service.get_personalization(
        prefs=prefs,
        song_database=song_database_dicts,
        liked_songs=liked_songs_dicts,
        history_songs=history_songs_dicts,
        local_time=local_time,
        local_day=local_day
    )

    # 4. Map returned recommendations back to full SongResponse details
    recommended_tracks = []
    for r in personalization_result.get("recommendations", []):
        s_id = r["song_id"]
        song_model = db.query(Song).filter(Song.id == s_id).first()
        if song_model:
            track_response = SongResponse(
                id=song_model.id,
                spotify_id=song_model.spotify_id,
                title=song_model.title,
                artist=song_model.artist,
                album=song_model.album,
                duration=song_model.duration,
                image_url=song_model.image_url,
                reason=r.get("reason"),
                preview_offset=r.get("preview_offset")
            )
            recommended_tracks.append(track_response)

    response_payload = RecommendationFeedResponse(
        tracks=recommended_tracks,
        ai_commentary=personalization_result.get("ai_commentary")
    )

    # Cache for 10 minutes
    cache.set(cache_key, response_payload, 600)
    return response_payload

