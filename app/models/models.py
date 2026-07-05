from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    avatar = Column(String, nullable=True)
    preferences = Column(String, nullable=True)  # JSON-serialized string of user preferences
    created_at = Column(DateTime, default=datetime.utcnow)

class Song(Base):
    __tablename__ = "songs"
    id = Column(String, primary_key=True, index=True)  # unique string ID
    spotify_id = Column(String, unique=True, nullable=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String, nullable=False)
    duration = Column(String, nullable=False)  # e.g., "4:12"
    image_url = Column(String, nullable=True)

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    playlist_id = Column(String, ForeignKey("playlists.id", ondelete="CASCADE"))
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"))
    position = Column(Integer, default=0)
    
    __table_args__ = (
        PrimaryKeyConstraint("playlist_id", "song_id"),
    )

class Like(Base):
    __tablename__ = "likes"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "song_id"),
    )

class History(Base):
    __tablename__ = "history"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"))
    played_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "song_id", "played_at"),
    )
