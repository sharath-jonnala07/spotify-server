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
    reason: Optional[str] = None
    preview_offset: Optional[int] = None

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

class RoutineTimePeriod(BaseModel):
    id: str
    startTime: str
    endTime: str
    days: List[str]

class UserStory(BaseModel):
    id: str
    text: str
    active: bool
    routineActive: bool
    routines: List[RoutineTimePeriod]

class UserPreferences(BaseModel):
    languages: List[str]
    vibe: str
    artists: List[str]
    custom_vibe: Optional[str] = None
    audio_focus: str = "vibe"
    custom_notes: Optional[str] = None
    discovery_appetite: int = 50  # 0 = Familiar, 100 = Curious
    exploration_depth_width: int = 50  # 0 = Depth, 100 = Width
    stories: List[UserStory] = []

class UserPreferencesResponse(BaseModel):
    status: str
    preferences: UserPreferences

class RecommendationFeedResponse(BaseModel):
    tracks: List[SongResponse]
    ai_commentary: Optional[str] = None


