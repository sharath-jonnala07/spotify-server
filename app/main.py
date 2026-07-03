from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.preloader import preload_database
from app.api.api import api_router

from app.models.models import User, Song, Playlist, PlaylistSong, Like, History

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio
from app.core.cache import cache
from app.services.resolver_service import resolver_service

async def warm_cache_background():
    await asyncio.sleep(2)  # Wait for startup to complete
    db = SessionLocal()
    try:
        songs = db.query(Song).filter(
            Song.id.like("eng_%") | Song.id.like("hin_%") | Song.id.like("tel_%")
        ).all()
        print(f"Pre-warming cache for {len(songs)} preloaded tracks...")
        for song in songs:
            try:
                await resolver_service.resolve_track(song.id, db)
                print(f"Cache warmed successfully for: {song.title} ({song.id})")
            except Exception as e:
                print(f"Failed to pre-warm cache for {song.id}: {e}")
    finally:
        db.close()

# Seed database on application startup
@app.on_event("startup")
async def startup_event():
    # Clear in-memory cache on startup to avoid stale URLs
    cache.clear()
    
    db = SessionLocal()
    try:
        preload_database(db)
    finally:
        db.close()

    # Warm cache in the background
    asyncio.create_task(warm_cache_background())

# Include global routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "docs": "/docs"
    }
