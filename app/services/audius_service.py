import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

class AudiusService:
    def __init__(self):
        self.base_url = settings.AUDIUS_BASE_URL
        self._headers = {"Accept": "application/json"}

    async def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/v1/tracks/search"
        params = {"query": query}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params, headers=self._headers, timeout=6.0)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    return [
                        {
                            "id": f"audius_{t['id']}",
                            "title": t["title"],
                            "artist": t["user"]["name"] if "user" in t else "Unknown Artist",
                            "album": "Audius Release",
                            "duration": self._seconds_to_min_sec(t.get("duration", 0)),
                            "image_url": t.get("artwork", {}).get("150x150") or t.get("artwork", {}).get("480x480")
                        }
                        for t in data
                    ]
        except Exception as e:
            print(f"Audius search failed: {e}")
        return []

    async def check_availability(self, title: str, artist: str) -> Optional[str]:
        query = f"{title} {artist}"
        tracks = await self.search_tracks(query)
        if not tracks:
            return None
            
        # Match closely. Verify if title overlaps significantly
        title_words = set(title.lower().split())
        for t in tracks[:4]:
            t_title_words = set(t["title"].lower().split())
            # If at least 50% of the original title words are present, consider it a match
            overlap = title_words.intersection(t_title_words)
            if len(overlap) >= max(1, len(title_words) // 2):
                track_id = t["id"].replace("audius_", "")
                return f"{self.base_url}/v1/tracks/{track_id}/stream"
        return None

    async def get_trending_tracks(self, limit: int = 15) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/v1/tracks/trending"
        params = {"limit": limit}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params, headers=self._headers, timeout=6.0)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    return [
                        {
                            "id": f"audius_{t['id']}",
                            "title": t["title"],
                            "artist": t["user"]["name"] if "user" in t else "Unknown Artist",
                            "album": "Audius Trending",
                            "duration": self._seconds_to_min_sec(t.get("duration", 0)),
                            "image_url": t.get("artwork", {}).get("150x150") or t.get("artwork", {}).get("480x480") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&auto=format&fit=crop&q=60"
                        }
                        for t in data
                    ]
        except Exception as e:
            print(f"Audius trending failed: {e}")
        return []

    def _seconds_to_min_sec(self, seconds: int) -> str:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

audius_service = AudiusService()
