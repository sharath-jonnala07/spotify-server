import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.cache import cache
from app.services.spotify_service import spotify_service
from app.services.audius_service import audius_service
from app.services.piped_service import piped_service
from app.models.models import Song

class ResolverService:
    def __init__(self):
        # 1 hour stream caching
        self.stream_ttl = 3600 

    async def resolve_track(self, track_id: str, db: Session) -> Optional[Dict[str, Any]]:
        # 1. Check in-memory cache first
        cached_result = cache.get(f"stream_{track_id}")
        if cached_result:
            print(f"Stream cache hit for: {track_id}")
            return cached_result

        # 2. Local database track check (preloaded/hybrid tracks)
        if track_id.startswith("local_") or track_id.startswith("song-"):
            # Fetch from DB
            song_record = db.query(Song).filter(Song.id == track_id).first()
            if song_record:
                # If it's a local track, we can resolve its audio URL (defaulting to SoundHelix mock streams)
                # or find if we need to resolve it via Audius/YT.
                # In this project, local songs already have direct public MP3 URLs stored in image/audio url.
                result = {
                    "trackId": song_record.id,
                    "title": song_record.title,
                    "artist": song_record.artist,
                    "album": song_record.album,
                    "coverImage": song_record.image_url,
                    # We will store the direct audio stream URL in the database or config
                    "streamUrl": self._get_local_audio_url(song_record.id),
                    "provider": "local"
                }
                cache.set(f"stream_{track_id}", result, self.stream_ttl)
                return result

        # 3. Direct YouTube Track resolution
        if track_id.startswith("youtube_"):
            video_id = track_id.replace("youtube_", "")
            # Retrieve stream details
            stream_url = await piped_service.get_stream_url(video_id)
            if stream_url:
                # Fetch metadata if in database
                song_record = db.query(Song).filter(Song.id == track_id).first()
                result = {
                    "trackId": track_id,
                    "title": song_record.title if song_record else "YouTube Track",
                    "artist": song_record.artist if song_record else "YouTube Artist",
                    "album": song_record.album if song_record else "YouTube",
                    "coverImage": song_record.image_url if song_record else "",
                    "streamUrl": stream_url,
                    "provider": "youtube"
                }
                cache.set(f"stream_{track_id}", result, self.stream_ttl)
                return result

        # 4. Direct Audius Track resolution
        if track_id.startswith("audius_"):
            audius_id = track_id.replace("audius_", "")
            
            # Check database first
            song_record = db.query(Song).filter(Song.id == track_id).first()
            if song_record:
                result = {
                    "trackId": track_id,
                    "title": song_record.title,
                    "artist": song_record.artist,
                    "album": song_record.album,
                    "coverImage": song_record.image_url,
                    "streamUrl": f"{audius_service.base_url}/v1/tracks/{audius_id}/stream",
                    "provider": "audius"
                }
                cache.set(f"stream_{track_id}", result, self.stream_ttl)
                return result

            # Query Audius API for metadata
            try:
                async with httpx.AsyncClient() as client:
                    url = f"{audius_service.base_url}/v1/tracks/{audius_id}"
                    res = await client.get(url, headers=audius_service._headers, timeout=5.0)
                    if res.status_code == 200:
                        track_data = res.json().get("data", {})
                        title = track_data.get("title", "Audius Track")
                        artist = track_data.get("user", {}).get("name") or "Audius Artist"
                        coverImage = track_data.get("artwork", {}).get("150x150") or track_data.get("artwork", {}).get("480x480") or ""
                        duration_secs = track_data.get("duration", 200)
                        
                        result = {
                            "trackId": track_id,
                            "title": title,
                            "artist": artist,
                            "album": "Audius Single",
                            "coverImage": coverImage,
                            "streamUrl": f"{audius_service.base_url}/v1/tracks/{audius_id}/stream",
                            "provider": "audius"
                        }
                        
                        # Store in database for future lookups
                        new_song = Song(
                            id=track_id,
                            title=title,
                            artist=artist,
                            album="Audius Single",
                            duration=audius_service._seconds_to_min_sec(duration_secs),
                            image_url=coverImage
                        )
                        db.add(new_song)
                        db.commit()
                        
                        cache.set(f"stream_{track_id}", result, self.stream_ttl)
                        return result
            except Exception as e:
                print(f"Audius metadata query failed: {e}")

            # Return absolute fallback
            result = {
                "trackId": track_id,
                "title": "Audius Track",
                "artist": "Audius Artist",
                "album": "Audius Single",
                "coverImage": "",
                "streamUrl": f"{audius_service.base_url}/v1/tracks/{audius_id}/stream",
                "provider": "audius"
            }
            cache.set(f"stream_{track_id}", result, self.stream_ttl)
            return result

        # 5. Spotify Track resolution (Requires music source resolution logic)
        spotify_id = track_id.replace("spotify_", "")
        
        # Get Spotify Metadata
        song_record = db.query(Song).filter(Song.id == track_id).first()
        title, artist, album, cover_image = "", "", "", ""
        
        if song_record:
            title = song_record.title
            artist = song_record.artist
            album = song_record.album
            cover_image = song_record.image_url
        else:
            # Fetch dynamically from Spotify if not cached in DB
            # We'll use client credential details
            token = await spotify_service._get_access_token()
            if token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    async with httpx.AsyncClient() as client:
                        res = await client.get(f"https://api.spotify.com/v1/tracks/{spotify_id}", headers=headers, timeout=5.0)
                        if res.status_code == 200:
                            data = res.json()
                            title = data["name"]
                            artist = ", ".join([a["name"] for a in data["artists"]])
                            album = data["album"]["name"]
                            cover_image = data["album"]["images"][0]["url"] if data["album"]["images"] else ""
                except Exception as e:
                    print(f"Spotify details lookup failed: {e}")

        if not title:
            # If metadata could not be resolved, return None
            return None

        # --- Music Source Resolution Tree ---
        
        # Step A: Check YouTube/yt-dlp first for official mainstream releases
        # (eng_, hin_, tel_, and spotify_ tracks) to ensure the official version is loaded.
        is_mainstream = (
            track_id.startswith("eng_") or 
            track_id.startswith("hin_") or 
            track_id.startswith("tel_") or 
            track_id.startswith("spotify_")
        )
        
        if is_mainstream:
            print(f"Resolving official track directly from YouTube: {title} - {artist}")
            yt_tracks = await piped_service.search_tracks(f"{title} {artist} official audio")
            if yt_tracks:
                video_id = yt_tracks[0]["id"].replace("youtube_", "")
                print(f"Resolving YouTube stream for videoId: {video_id}")
                yt_stream = await piped_service.get_stream_url(video_id)
                if yt_stream:
                    result = {
                        "trackId": track_id,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "coverImage": cover_image,
                        "streamUrl": yt_stream,
                        "provider": "youtube"
                    }
                    cache.set(f"stream_{track_id}", result, self.stream_ttl)
                    return result

        # Step B: Check Audius Availability (for non-mainstream or if YouTube resolution fails)
        print(f"Checking Audius availability for: {title} - {artist}")
        audius_stream = await audius_service.check_availability(title, artist)
        if audius_stream:
            print(f"Found Audius match for: {title}")
            result = {
                "trackId": track_id,
                "title": title,
                "artist": artist,
                "album": album,
                "coverImage": cover_image,
                "streamUrl": audius_stream,
                "provider": "audius"
            }
            cache.set(f"stream_{track_id}", result, self.stream_ttl)
            return result

        # Step C: Search YouTube as final fallback if not already tried
        if not is_mainstream:
            print(f"Audius match not found. Searching YouTube fallback for: {title} - {artist}")
            yt_tracks = await piped_service.search_tracks(f"{title} {artist}")
            if yt_tracks:
                video_id = yt_tracks[0]["id"].replace("youtube_", "")
                print(f"Resolving YouTube stream for videoId: {video_id}")
                yt_stream = await piped_service.get_stream_url(video_id)
                if yt_stream:
                    result = {
                        "trackId": track_id,
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "coverImage": cover_image,
                        "streamUrl": yt_stream,
                        "provider": "youtube"
                    }
                    cache.set(f"stream_{track_id}", result, self.stream_ttl)
                    return result

        return None


    def _get_local_audio_url(self, song_id: str) -> str:
        # Map local song IDs to public copyright-free SoundHelix streams
        # Same list as frontend mock database
        num = 1
        if "song-" in song_id:
            try:
                num = int(song_id.replace("song-", ""))
            except:
                pass
        return f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{num}.mp3"

resolver_service = ResolverService()
