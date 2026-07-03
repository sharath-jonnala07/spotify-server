import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.schemas import PlaylistCreate, PlaylistResponse, PlaylistUpdate, SongResponse
from app.models.models import Playlist, PlaylistSong, Song, User
from datetime import datetime

router = APIRouter()
DEFAULT_USER_ID = "default"

@router.post("/", response_model=PlaylistResponse)
def create_playlist(playlist_in: PlaylistCreate, db: Session = Depends(get_db)):
    playlist_id = f"playlist-{uuid.uuid4()}"
    new_playlist = Playlist(
        id=playlist_id,
        user_id=DEFAULT_USER_ID,
        name=playlist_in.name,
        description=playlist_in.description,
        created_at=datetime.utcnow()
    )
    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)
    
    # Return empty songs list initially
    response = PlaylistResponse.from_orm(new_playlist)
    response.songs = []
    return response

@router.get("/", response_model=List[PlaylistResponse])
def list_playlists(db: Session = Depends(get_db)):
    playlists = (
        db.query(Playlist)
        .filter(Playlist.user_id == DEFAULT_USER_ID)
        .order_by(Playlist.created_at.desc())
        .all()
    )
    
    responses = []
    for playlist in playlists:
        # Get songs in playlist ordered by position
        songs = (
            db.query(Song)
            .join(PlaylistSong, PlaylistSong.song_id == Song.id)
            .filter(PlaylistSong.playlist_id == playlist.id)
            .order_by(PlaylistSong.position.asc())
            .all()
        )
        resp = PlaylistResponse.from_orm(playlist)
        resp.songs = [SongResponse.from_orm(s) for s in songs]
        responses.append(resp)
    return responses

@router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(playlist_id: str, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == DEFAULT_USER_ID).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    songs = (
        db.query(Song)
        .join(PlaylistSong, PlaylistSong.song_id == Song.id)
        .filter(PlaylistSong.playlist_id == playlist.id)
        .order_by(PlaylistSong.position.asc())
        .all()
    )
    resp = PlaylistResponse.from_orm(playlist)
    resp.songs = [SongResponse.from_orm(s) for s in songs]
    return resp

@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(playlist_id: str, playlist_in: PlaylistUpdate, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == DEFAULT_USER_ID).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    playlist.name = playlist_in.name
    playlist.description = playlist_in.description
    db.commit()
    db.refresh(playlist)
    
    songs = (
        db.query(Song)
        .join(PlaylistSong, PlaylistSong.song_id == Song.id)
        .filter(PlaylistSong.playlist_id == playlist.id)
        .order_by(PlaylistSong.position.asc())
        .all()
    )
    resp = PlaylistResponse.from_orm(playlist)
    resp.songs = [SongResponse.from_orm(s) for s in songs]
    return resp

@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: str, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == DEFAULT_USER_ID).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    db.delete(playlist)
    db.commit()
    return {"status": "success", "message": "Playlist deleted successfully"}

@router.post("/{playlist_id}/songs/{track_id}", response_model=PlaylistResponse)
def add_song_to_playlist(
    playlist_id: str,
    track_id: str,
    title: str = Query(...),
    artist: str = Query(...),
    album: str = Query(...),
    cover_image: str = Query(""),
    db: Session = Depends(get_db)
):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == DEFAULT_USER_ID).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

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

    # Check if already in playlist
    existing = db.query(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == track_id).first()
    if not existing:
        # Determine next position
        count = db.query(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id).count()
        new_ps = PlaylistSong(
            playlist_id=playlist_id,
            song_id=track_id,
            position=count
        )
        db.add(new_ps)
        db.commit()
        
    return get_playlist(playlist_id, db)

@router.delete("/{playlist_id}/songs/{track_id}", response_model=PlaylistResponse)
def remove_song_from_playlist(playlist_id: str, track_id: str, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == DEFAULT_USER_ID).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    ps = db.query(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == track_id).first()
    if ps:
        db.delete(ps)
        db.commit()
        
        # Shift remaining tracks positions
        remaining = (
            db.query(PlaylistSong)
            .filter(PlaylistSong.playlist_id == playlist_id)
            .order_by(PlaylistSong.position.asc())
            .all()
        )
        for idx, item in enumerate(remaining):
            item.position = idx
        db.commit()
        
    return get_playlist(playlist_id, db)
