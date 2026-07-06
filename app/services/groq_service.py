import os
import json
import httpx
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings

class GroqService:
    def __init__(self):
        # Load GROQ_API_KEY from environment
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_story_active(self, story: Dict[str, Any], local_time: Optional[str] = None, local_day: Optional[str] = None) -> bool:
        """
        Determines if a story is active based on its active state and optional routine schedules.
        """
        if not story.get("active", False):
            return False
            
        # If routine is not active, the story is manually active
        if not story.get("routineActive", False):
            return True
            
        current_time_str = local_time
        current_day = local_day

        if not current_time_str or not current_day:
            # Fallback to server local time
            local_now = datetime.datetime.now()
            current_time_str = local_now.strftime("%H:%M")
            days_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            current_day = days_map[local_now.weekday()]

        try:
            current_hour, current_minute = map(int, current_time_str.split(":"))
            current_minutes_since_midnight = current_hour * 60 + current_minute
        except Exception:
            return True  # Fallback to active if parsing fails

        routines = story.get("routines", [])
        if not routines:
            return True # Toggled active but no routines defined means always active

        for routine in routines:
            days = routine.get("days", [])
            day_matched = False
            for d in days:
                if d.lower().startswith(current_day.lower()[:3]):
                    day_matched = True
                    break
            
            if not day_matched:
                continue
                
            # Check time range match
            try:
                start_h, start_m = map(int, routine.get("startTime", "00:00").split(":"))
                end_h, end_m = map(int, routine.get("endTime", "23:59").split(":"))
                
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                
                if start_minutes <= end_minutes:
                    if start_minutes <= current_minutes_since_midnight <= end_minutes:
                        return True
                else:
                    # Overnight range (e.g. 22:00 to 04:00)
                    if current_minutes_since_midnight >= start_minutes or current_minutes_since_midnight <= end_minutes:
                        return True
            except Exception:
                continue
                
        return False

    async def get_personalization(
        self,
        prefs: Dict[str, Any],
        song_database: List[Dict[str, Any]],
        liked_songs: List[Dict[str, Any]],
        history_songs: List[Dict[str, Any]],
        local_time: Optional[str] = None,
        local_day: Optional[str] = None,
        playlist_id: Optional[str] = None,
        playlist_songs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point to get AI DJ commentary & structured song recommendations.
        """
        # 1. Resolve active stories
        stories = prefs.get("stories", [])
        active_stories = [s for s in stories if self.is_story_active(s, local_time, local_day)]
        
        # 2. Extract dials
        discovery_appetite = prefs.get("discovery_appetite", 50)
        exploration_depth_width = prefs.get("exploration_depth_width", 50)
        
        # Check if Groq API key is present
        api_key = self.api_key or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            print("Groq API key not configured. Falling back to local heuristic recommendations.")
            return self._local_fallback_recommendations(
                prefs, active_stories, discovery_appetite, exploration_depth_width,
                song_database, liked_songs, history_songs, playlist_id, playlist_songs
            )

        # 3. Formulate Prompt
        prompt = self._build_prompt(
            prefs, active_stories, discovery_appetite, exploration_depth_width,
            song_database, liked_songs, history_songs, playlist_id, playlist_songs
        )

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Adjust limit based on whether it is a playlist or main home feed recommendation
            limit_count = 4 if playlist_id else 8
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are the Spotify Horizon AI DJ, a premium, hyper-personalized music recommender system "
                            "designed for a Stanford GSB presentation. You represent state-of-the-art enterprise-grade AI.\n"
                            "You must respond ONLY with a valid JSON object matching this schema:\n"
                            "{\n"
                            "  \"recommendations\": [\n"
                            "    {\n"
                            "      \"song_id\": \"string (must match one of the available IDs exactly)\",\n"
                            "      \"reason\": \"string (a brief, premium 1-sentence explanation of why this song fits their dials and active story context)\",\n"
                            "      \"preview_offset\": int (number of seconds to start playing from, targeting the chorus or hook, usually between 30 and 90)\n"
                            "    }\n"
                            "  ],\n"
                            "  \"ai_commentary\": \"string (a short, engaging 2-sentence Spotify DJ intro welcoming the user, addressing their active stories and dials, and introducing the playlist)\"\n"
                            "}\n"
                            f"Ensure that the recommendations array contains exactly {limit_count} songs from the available list.\n"
                            "Return ONLY the raw JSON string without markdown code fences or backticks."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }

            async with httpx.AsyncClient() as client:
                res = await client.post(self.api_url, headers=headers, json=payload, timeout=20.0)
                if res.status_code == 200:
                    response_data = res.json()
                    content = response_data["choices"][0]["message"]["content"]
                    result = json.loads(content)
                    
                    # Validate song IDs are in the database
                    validated_recs = []
                    db_song_ids = {s["id"] for s in song_database}
                    
                    for rec in result.get("recommendations", []):
                        s_id = rec.get("song_id")
                        if s_id in db_song_ids:
                            validated_recs.append(rec)
                            
                    if not validated_recs:
                        raise Exception("LLM returned no valid song IDs from database.")
                        
                    result["recommendations"] = validated_recs
                    return result
                else:
                    print(f"Groq API error: status={res.status_code}, body={res.text}")
                    raise Exception(f"Groq API returned error status {res.status_code}")
                    
        except Exception as e:
            print(f"Failed to fetch personalization from Groq: {e}. Falling back to local heuristics.")
            return self._local_fallback_recommendations(
                prefs, active_stories, discovery_appetite, exploration_depth_width,
                song_database, liked_songs, history_songs, playlist_id, playlist_songs
            )

    def _build_prompt(
        self,
        prefs: Dict[str, Any],
        active_stories: List[Dict[str, Any]],
        discovery_appetite: int,
        exploration_depth_width: int,
        song_database: List[Dict[str, Any]],
        liked_songs: List[Dict[str, Any]],
        history_songs: List[Dict[str, Any]],
        playlist_id: Optional[str] = None,
        playlist_songs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Assembles the information for the LLM prompt.
        """
        languages = prefs.get("languages", [])
        vibe = prefs.get("vibe", "")
        custom_vibe = prefs.get("custom_vibe", "")
        audio_focus = prefs.get("audio_focus", "vibe")
        custom_notes = prefs.get("custom_notes", "")
        fav_artists = prefs.get("artists", [])

        liked_song_details = [f"'{s['title']}' by {s['artist']}" for s in liked_songs]
        history_details = [f"'{s['title']}' by {s['artist']}" for s in history_songs[:5]]
        story_details = [s.get("text", "") for s in active_stories]

        available_tracks = [
            f"ID: '{s['id']}', Title: '{s['title']}', Artist: '{s['artist']}', Album: '{s['album']}'"
            for s in song_database
            if not s["id"].startswith("pod_")
        ]

        if playlist_id:
            existing_tracks = []
            if playlist_songs:
                existing_tracks = [s["id"] for s in playlist_songs]
            
            prompt = (
                f"### CONTEXT: PLAYLIST DISCOVERY RECOMMENDATIONS\n"
                f"The user wants recommendations for unfamiliar songs to ADD to their playlist (ID: '{playlist_id}').\n"
                f"Existing track IDs in this playlist: {existing_tracks}\n"
                f"You MUST exclude these existing tracks from your suggestions.\n\n"
            )
        else:
            prompt = "### CONTEXT: HOME FEED RECOMMENDATIONS\n\n"

        prompt += (
            f"### USER EXPLORATION DIALS (EXPLORATION BUDGET)\n"
            f"- Discovery Appetite (Familiar vs Curious): {discovery_appetite}/100. "
            f"(0 = Recommend only familiar tracks matching liked songs/artists. 100 = Adventurous curiosity, recommend only songs and artists they have never heard/liked before).\n"
            f"- Sonic Breadth (Depth vs Width): {exploration_depth_width}/100. "
            f"(0 = Depth, stick strictly to their favorite languages/genres. 100 = Width, recommend a highly diverse mix across unexpected languages and styles).\n\n"
            
            f"### ACTIVE CONTEXT STORIES (ROUTINE SCHEDULES)\n"
            f"The user has defined the following active scenarios/routines right now:\n"
            f"{' - ' + ', '.join(story_details) if story_details else 'No active routine stories at this moment.'}\n\n"
            
            f"### USER MUSIC PROFILE\n"
            f"- Preferred Languages: {languages}\n"
            f"- Favorite Artists: {fav_artists}\n"
            f"- Focus Vibe: {vibe} {(' (Custom: ' + custom_vibe + ')') if custom_vibe else ''}\n"
            f"- Audio Layer Focus: {audio_focus}\n"
            f"- Custom Notes: {custom_notes}\n"
            f"- Liked Songs: {liked_song_details}\n"
            f"- Recent Play History: {history_details}\n\n"

            f"### AVAILABLE SONGS DATABASE (Select ONLY from this list, using exact IDs)\n"
        )
        prompt += "\n".join(available_tracks) + "\n\n"
        
        if playlist_id:
            prompt += (
                f"Provide exactly 3 to 4 song recommendations from the available list. "
                f"Since these are UNFAMILIAR suggestions, prioritize songs the user has NOT liked or listened to, "
                f"balancing it with their Depth/Width settings and active routines. Make the reasons sound personalized."
            )
        else:
            prompt += (
                f"Provide exactly 6 to 8 song recommendations from the available list, ordered by relevance. "
                f"Tailor the mix to their current active stories and dials. If Appetite is low, include some liked songs. "
                f"Generate a premium AI DJ commentary intro matching this mix."
            )
            
        return prompt

    def _local_fallback_recommendations(
        self,
        prefs: Dict[str, Any],
        active_stories: List[Dict[str, Any]],
        discovery_appetite: int,
        exploration_depth_width: int,
        song_database: List[Dict[str, Any]],
        liked_songs: List[Dict[str, Any]],
        history_songs: List[Dict[str, Any]],
        playlist_id: Optional[str] = None,
        playlist_songs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        A local heuristic recommender that mimics the LLM's dials and context matching logic.
        """
        db_songs = [s for s in song_database if not s["id"].startswith("pod_")]
        liked_ids = {s["id"] for s in liked_songs}
        history_ids = {s["id"] for s in history_songs}
        
        routine_texts = [s.get("text", "").lower() for s in active_stories]
        is_gym = any("gym" in t or "workout" in t or "run" in t or "active" in t for t in routine_texts)
        is_chill = any("chill" in t or "sleep" in t or "relax" in t or "night" in t for t in routine_texts)
        is_focus = any("study" in t or "work" in t or "focus" in t or "exam" in t for t in routine_texts)

        playlist_ids = set()
        if playlist_songs:
            playlist_ids = {s["id"] for s in playlist_songs}

        scored_songs = []
        for song in db_songs:
            if playlist_id and song["id"] in playlist_ids:
                continue

            score = 50
            
            is_familiar = song["id"] in liked_ids or song["id"] in history_ids or any(art.lower() in song["artist"].lower() for art in prefs.get("artists", []))
            
            if is_familiar:
                score += (50 - discovery_appetite) * 0.8
            else:
                score += (discovery_appetite - 50) * 0.8

            song_lang = song["id"].split("_")[0]
            pref_langs = [l.lower() for l in prefs.get("languages", [])]
            
            lang_match = False
            for pl in pref_langs:
                if pl.startswith("eng") and song_lang == "eng": lang_match = True
                elif pl.startswith("hin") and song_lang == "hin": lang_match = True
                elif pl.startswith("tel") and song_lang == "tel": lang_match = True
                elif pl.startswith("tam") and song_lang == "tam": lang_match = True
                elif pl.startswith("kan") and song_lang == "kan": lang_match = True
                elif pl.startswith("mal") and song_lang == "mal": lang_match = True
            
            if lang_match:
                score += (50 - exploration_depth_width) * 0.6
            else:
                score += (exploration_depth_width - 50) * 0.6

            song_title = song["title"].lower()
            if is_gym:
                if song_title in ["naatu naatu", "blinding lights", "shape of you", "stay", "ranjithame", "ra ra rakkamma"]:
                    score += 40
            elif is_chill or is_focus:
                if song_title in ["kabira", "tum hi ho", "flowers", "apna bana le", "srivalli", "samajavaragamana", "adiga adiga", "darshana"]:
                    score += 40

            user_vibe = prefs.get("vibe", "").lower()
            if user_vibe == "energy" and song_title in ["naatu naatu", "blinding lights", "stay"]:
                score += 15
            elif user_vibe == "relax" and song_title in ["tum hi ho", "apna bana le", "srivalli"]:
                score += 15

            import random
            score += random.uniform(-2, 2)
            
            scored_songs.append((song, score))

        scored_songs.sort(key=lambda x: x[1], reverse=True)

        limit = 4 if playlist_id else 6
        selected = scored_songs[:limit]
        
        recommendations = []
        for song, score in selected:
            song_lang = song["id"].split("_")[0].upper()
            is_liked = song["id"] in liked_ids
            
            if playlist_id:
                reason = f"Suggested in {song_lang} to expand your playlist horizon. Perfect fit for your width settings."
            else:
                if len(routine_texts) > 0:
                    reason = f"Personalized for your active routine: '{active_stories[0].get('text')}' based on your {discovery_appetite}% appetite dial."
                else:
                    reason = f"Tuned for your {user_vibe or 'daily'} vibe, matching your Horizon exploration preferences."
            
            recommendations.append({
                "song_id": song["id"],
                "reason": reason,
                "preview_offset": 45 if not is_liked else 0
            })

        if playlist_id:
            ai_commentary = None
        else:
            if active_stories:
                routine_name = active_stories[0].get("text")
                ai_commentary = f"Hey Sharath! Let's get going. Since you're currently in your '{routine_name}' routine, I've loaded up a mix that balances your comfortable favorites with a few fresh horizons. Tune in!"
            else:
                ai_commentary = f"Hey Sharath! Welcome back to Horizon. I've analyzed your dials and personal stories to draft this custom listening session. Let's see where the rhythm takes us today."

        return {
            "recommendations": recommendations,
            "ai_commentary": ai_commentary
        }

groq_service = GroqService()
