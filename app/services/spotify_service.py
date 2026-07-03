import base64
import httpx
from typing import Dict, Any, List
from app.core.config import settings

class SpotifyService:
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.token_url = "https://accounts.spotify.com/api/token"
        self.search_url = "https://api.spotify.com/v1/search"
        self.rec_url = "https://api.spotify.com/v1/recommendations"

    async def _get_access_token(self) -> str:
        if not self.client_id or not self.client_secret:
            return ""
            
        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            headers = {"Authorization": f"Basic {b64_auth}"}
            data = {"grant_type": "client_credentials"}
            
            async with httpx.AsyncClient() as client:
                res = await client.post(self.token_url, headers=headers, data=data, timeout=5.0)
                if res.status_code == 200:
                    return res.json().get("access_token", "")
        except Exception as e:
            print(f"Spotify authentication failed: {e}")
        return ""

    async def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        token = await self._get_access_token()
        if not token:
            return []

        try:
            headers = {"Authorization": f"Bearer {token}"}
            params = {"q": query, "type": "track", "limit": 15}
            async with httpx.AsyncClient() as client:
                res = await client.get(self.search_url, headers=headers, params=params, timeout=5.0)
                if res.status_code == 200:
                    tracks = res.json().get("tracks", {}).get("items", [])
                    return [
                        {
                            "id": f"spotify_{t['id']}",
                            "spotify_id": t["id"],
                            "title": t["name"],
                            "artist": ", ".join([a["name"] for a in t["artists"]]),
                            "album": t["album"]["name"],
                            "duration": self._ms_to_min_sec(t["duration_ms"]),
                            "image_url": t["album"]["images"][0]["url"] if t["album"]["images"] else None
                        }
                        for t in tracks
                    ]
        except Exception as e:
            print(f"Spotify search failed: {e}")
        return []

    async def get_recommendations(self, seed_track_ids: List[str]) -> List[Dict[str, Any]]:
        token = await self._get_access_token()
        if not token or not seed_track_ids:
            return []

        try:
            headers = {"Authorization": f"Bearer {token}"}
            # Limit seeds to max 5 (Spotify constraint)
            params = {"seed_tracks": ",".join(seed_track_ids[:5]), "limit": 15}
            async with httpx.AsyncClient() as client:
                res = await client.get(self.rec_url, headers=headers, params=params, timeout=5.0)
                if res.status_code == 200:
                    tracks = res.json().get("tracks", [])
                    return [
                        {
                            "id": f"spotify_{t['id']}",
                            "spotify_id": t["id"],
                            "title": t["name"],
                            "artist": ", ".join([a["name"] for a in t["artists"]]),
                            "album": t["album"]["name"],
                            "duration": self._ms_to_min_sec(t["duration_ms"]),
                            "image_url": t["album"]["images"][0]["url"] if t["album"]["images"] else None
                        }
                        for t in tracks
                    ]
        except Exception as e:
            print(f"Spotify recommendations failed: {e}")
        return []

    def _ms_to_min_sec(self, ms: int) -> str:
        seconds = int(ms / 1000)
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

spotify_service = SpotifyService()
