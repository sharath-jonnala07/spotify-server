from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class SongBase(BaseModel):
    id: str
    spotify_id: Optional[str] = None
    title: str
    artist: str
    album: str
    duration: str
    image_url: Optional[str] = None

class SongCreate(SongBase):
    pass

class SongResponse(SongBase):
    class Config:
        from_attributes = True

class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(PlaylistBase):
    pass

class PlaylistResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    songs: List[SongResponse] = []

    class Config:
        from_attributes = True

class ResolvedTrack(BaseModel):
    trackId: str
    title: str
    artist: str
    album: str
    coverImage: str
    streamUrl: str
    provider: str  # "audius" or "youtube"

class SearchResponse(BaseModel):
    tracks: List[SongResponse]
