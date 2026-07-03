from fastapi import APIRouter
from app.api.endpoints import tracks, playlists, recommendations

api_router = APIRouter()

api_router.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
