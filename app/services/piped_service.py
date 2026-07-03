import yt_dlp
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings

class PipedService:
    def __init__(self):
        self.instances = settings.PIPED_INSTANCES
        self._current_instance_idx = 0

    async def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        print(f"yt-dlp search query: {query}")
        
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
        }
        
        loop = asyncio.get_event_loop()
        try:
            # Run yt_dlp blocking call in executor to keep it async-friendly
            def run_extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch5:{query}", download=False)
            
            info = await loop.run_in_executor(None, run_extract)
            
            results = []
            if info and 'entries' in info:
                for entry in info['entries']:
                    if not entry or 'id' not in entry:
                        continue
                    
                    video_id = entry['id']
                    duration_secs = entry.get('duration') or 0
                    duration_str = self._seconds_to_min_sec(int(duration_secs))
                    
                    thumbnails = entry.get('thumbnails', [])
                    image_url = ""
                    if thumbnails:
                        image_url = thumbnails[-1].get('url') or ""
                    
                    results.append({
                        "id": f"youtube_{video_id}",
                        "title": entry.get('title') or "YouTube Track",
                        "artist": entry.get('uploader') or entry.get('channel') or "YouTube Artist",
                        "album": "YouTube Single",
                        "duration": duration_str,
                        "image_url": image_url
                    })
            return results
        except Exception as e:
            print(f"yt-dlp search failed: {e}")
            return []

    async def get_stream_url(self, video_id: str) -> Optional[str]:
        print(f"yt-dlp stream resolution for video_id: {video_id}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
            'check_formats': 'skip',
        }
        
        loop = asyncio.get_event_loop()
        try:
            def run_extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            info = await loop.run_in_executor(None, run_extract)
            if info:
                return info.get('url')
        except Exception as e:
            print(f"yt-dlp stream resolution failed: {e}")
        return None

    def _seconds_to_min_sec(self, seconds: int) -> str:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

piped_service = PipedService()
