from sqlalchemy.orm import Session
from app.models.models import User, Song
from datetime import datetime

def preload_database(db: Session) -> None:
    # 0. Safe Schema Migration (Add preferences column to users table if missing)
    try:
        from sqlalchemy import text
        db.execute(text("ALTER TABLE users ADD COLUMN preferences TEXT"))
        db.commit()
        print("Schema migration: preferences column verified/added in users table.")
    except Exception as e:
        db.rollback()
        # preferences column already exists, which is fine

    # 1. Preload Default User
    try:
        default_user = db.query(User).filter(User.id == "default").first()
        if not default_user:
            new_user = User(
                id="default",
                name="Sharath",
                email="sharath@spotify.local",
                avatar=None,
                preferences=None,
                created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            print("Default user preloaded.")
    except Exception as e:
        db.rollback()
        print(f"Skipping user preload (likely already exists or handled by another worker): {e}")

    # 2. Preload Hybrid Baseline Tracks (English, Hindi, Telugu hits, and Podcasts)
    baseline_songs = [
        # English
        {
            "id": "eng_1",
            "spotify_id": "7qiZRh2GesKMm28rRI5q66",
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "album": "Divide",
            "duration": "3:53",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/15/e6/e8/15e6e8a4-4190-6a8b-86c3-ab4a51b88288/190295851286.jpg/600x600bb.jpg"
        },
        {
            "id": "eng_2",
            "spotify_id": "0V3wPSX3ygokj7v2EXj6v1",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "duration": "3:20",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/a6/6e/bf/a66ebf79-5008-8948-b352-a790fc87446b/19UM1IM04638.rgb.jpg/600x600bb.jpg"
        },
        {
            "id": "eng_3",
            "spotify_id": "4D7t7TTzfs2Rhw29ycu85X",
            "title": "As It Was",
            "artist": "Harry Styles",
            "album": "Harry's House",
            "duration": "2:47",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/2a/19/fb/2a19fb85-2f70-9e44-f2a9-82abe679b88e/886449990061.jpg/600x600bb.jpg"
        },
        {
            "id": "eng_4",
            "spotify_id": "5Pbee1XvhcZZpcse7JuLYA",
            "title": "Stay",
            "artist": "The Kid LAROI, Justin Bieber",
            "album": "F*CK LOVE 3: OVER YOU",
            "duration": "2:21",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/89/59/6a/89596ab9-fa3c-8d08-4d95-a6450fa2013c/886449400515.jpg/600x600bb.jpg"
        },
        {
            "id": "eng_5",
            "spotify_id": "0y602COQ2dfHGHG3FFG5HG",
            "title": "Flowers",
            "artist": "Miley Cyrus",
            "album": "Endless Summer Vacation",
            "duration": "3:20",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/8c/67/ff/8c67ff91-31c3-3fef-1884-ce3ec89f3af4/196589946874.jpg/600x600bb.jpg"
        },
        # Hindi
        {
            "id": "hin_1",
            "spotify_id": "1tK4v94j5J137W4229ycuX",
            "title": "Tum Hi Ho",
            "artist": "Arijit Singh, Mithoon",
            "album": "Aashiqui 2",
            "duration": "4:22",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/bb/23/ee/bb23eeed-0c35-4f1d-2b11-485622777ae4/8902894353007_cover.jpg/600x600bb.jpg"
        },
        {
            "id": "hin_2",
            "spotify_id": "4664v94j5J137W4229ycuY",
            "title": "Kesariya",
            "artist": "Arijit Singh, Pritam",
            "album": "Brahmastra",
            "duration": "4:28",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/9f/13/ca/9f13ca3b-e533-03e0-f19a-f0aaa774581d/196589311191.jpg/600x600bb.jpg"
        },
        {
            "id": "hin_3",
            "spotify_id": "7664v94j5J137W4229ycuZ",
            "title": "Apna Bana Le",
            "artist": "Arijit Singh, Sachin-Jigar",
            "album": "Bhediya",
            "duration": "4:21",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/2e/0b/c0/2e0bc070-112f-a827-6ad8-6bc64f7caaff/840214460180.png/600x600bb.jpg"
        },
        {
            "id": "hin_4",
            "spotify_id": "8664v94j5J137W4229ycuW",
            "title": "Raataan Lambiyan",
            "artist": "Jubin Nautiyal, Asees Kaur",
            "album": "Shershaah",
            "duration": "3:50",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/61/65/ae/6165aee9-8bb9-0bd4-02b0-5d0f1e6257a3/886449510238.jpg/600x600bb.jpg"
        },
        {
            "id": "hin_5",
            "spotify_id": "9664v94j5J137W4229ycuV",
            "title": "Kabira",
            "artist": "Tochi Raina, Rekha Bhardwaj",
            "album": "Yeh Jawaani Hai Deewani",
            "duration": "4:11",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/62/d6/74/62d67432-0670-631f-db6a-d4bac3adae4b/8902894353328_cover.jpg/600x600bb.jpg"
        },
        # Telugu
        {
            "id": "tel_1",
            "spotify_id": "0y74v94j5J137W4229ycuA",
            "title": "Naatu Naatu",
            "artist": "Rahul Sipligunj, Kaala Bhairava",
            "album": "RRR",
            "duration": "3:35",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/dd/39/14/dd3914e5-a2f3-b355-51f3-9a1f0e3ca246/8903431853592_cover.jpg/600x600bb.jpg"
        },
        {
            "id": "tel_2",
            "spotify_id": "1y74v94j5J137W4229ycuB",
            "title": "Samajavaragamana",
            "artist": "Sid Sriram",
            "album": "Ala Vaikunthapurramuloo",
            "duration": "3:41",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/53/98/c1/5398c1cf-7c16-24a6-bfa3-391dc6015376/cover.jpg/600x600bb.jpg"
        },
        {
            "id": "tel_3",
            "spotify_id": "2y74v94j5J137W4229ycuC",
            "title": "Srivalli",
            "artist": "Sid Sriram",
            "album": "Pushpa: The Rise",
            "duration": "3:44",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/ec/34/7b/ec347b9b-0add-c529-4746-799277a5e1c0/cover.jpg/600x600bb.jpg"
        },
        {
            "id": "tel_4",
            "spotify_id": "3y74v94j5J137W4229ycuD",
            "title": "Butta Bomma",
            "artist": "Armaan Malik",
            "album": "Ala Vaikunthapurramuloo",
            "duration": "3:17",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/46/aa/48/46aa4863-c1ec-4574-e98e-80b8c1f3ef69/cover.jpg/600x600bb.jpg"
        },
        {
            "id": "tel_5",
            "spotify_id": "4y74v94j5J137W4229ycuE",
            "title": "Adiga Adiga",
            "artist": "Sid Sriram",
            "album": "Ninnu Kori",
            "duration": "3:46",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/98/81/43/988143ca-e902-4e8a-977c-3e31eefcfaab/196925399784.jpg/600x600bb.jpg"
        },
        # Tamil
        {
            "id": "tam_1",
            "spotify_id": "tam_spotify_1",
            "title": "Arabic Kuthu",
            "artist": "Anirudh Ravichander, Jonita Gandhi",
            "album": "Beast",
            "duration": "4:40",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/e9/19/b9/e919b921-d5a8-9e9a-8508-3551da375aee/196626458629.jpg/600x600bb.jpg"
        },
        {
            "id": "tam_2",
            "spotify_id": "tam_spotify_2",
            "title": "Ranjithame",
            "artist": "Vijay, M. M. Manasi",
            "album": "Varisu",
            "duration": "4:48",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/b3/ef/82/b3ef8222-bb2e-3e78-6211-82bc8de47e50/8903431909152_cover.jpg/600x600bb.jpg"
        },
        # Kannada
        {
            "id": "kan_1",
            "spotify_id": "kan_spotify_1",
            "title": "Singara Siriye",
            "artist": "Vijay Prakash, Ananya Bhat",
            "album": "Kantara",
            "duration": "4:40",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/08/1e/a0/081ea00b-1dd6-876f-860a-a0add84d317e/8904337278427.jpg/600x600bb.jpg"
        },
        {
            "id": "kan_2",
            "spotify_id": "kan_spotify_2",
            "title": "Ra Ra Rakkamma",
            "artist": "Nakash Aziz, Sunidhi Chauhan",
            "album": "Vikrant Rona",
            "duration": "3:43",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/1c/50/3a/1c503af8-bfc0-4228-979d-b0a51370ef65/8903431880178_cover.jpg/600x600bb.jpg"
        },
        # Malayalam
        {
            "id": "mal_1",
            "spotify_id": "mal_spotify_1",
            "title": "Darshana",
            "artist": "Hesham Abdul Wahab, Darshana Rajendran",
            "album": "Hridayam",
            "duration": "3:46",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/69/26/34/6926341a-b85f-f853-de47-cb6fa81544aa/cover.jpg/600x600bb.jpg"
        },
        {
            "id": "mal_2",
            "spotify_id": "mal_spotify_2",
            "title": "Thallumaala Song",
            "artist": "Hrithik, Shebin",
            "album": "Thallumaala",
            "duration": "3:10",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/cd/4a/c2/cd4ac279-7384-5ea1-7dd4-716f20d2c837/cover.jpg/600x600bb.jpg"
        },
        # Podcasts (Seeding to make the Podcasts feature real)
        {
            "id": "pod_1",
            "spotify_id": "think_fast_talk_smart_1",
            "title": "Effective Communication in Business & Life",
            "artist": "Matt Abrahams, Stanford GSB",
            "album": "Think Fast, Talk Smart",
            "duration": "21:40",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Podcasts221/v4/0e/a3/48/0ea34886-96c0-8299-e16c-d039cfaedc78/mza_5307345217675863813.jpg/600x600bb.jpg"
        },
        {
            "id": "pod_2",
            "spotify_id": "lex_fridman_altman",
            "title": "Sam Altman: OpenAI, GPT-5, and the Future of AGI",
            "artist": "Lex Fridman",
            "album": "Lex Fridman Podcast",
            "duration": "2:10:00",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Podcasts115/v4/3e/e3/9c/3ee39c89-de08-47a6-7f3d-3849cef6d255/mza_16657851278549137484.png/600x600bb.jpg"
        },
        {
            "id": "pod_3",
            "spotify_id": "how_i_built_this_ek",
            "title": "Spotify: Daniel Ek",
            "artist": "Guy Raz",
            "album": "How I Built This",
            "duration": "54:20",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Podcasts126/v4/64/45/06/644506b5-c44f-f661-f74e-f63a4b2511bc/mza_14892199991035639268.jpeg/600x600bb.jpg"
        },
        {
            "id": "pod_4",
            "spotify_id": "acquired_spotify",
            "title": "The Complete History & Strategy of Spotify",
            "artist": "Ben Gilbert & David Rosenthal",
            "album": "Acquired Podcast",
            "duration": "3:42:00",
            "image_url": "https://is1-ssl.mzstatic.com/image/thumb/Podcasts211/v4/43/c5/fb/43c5fbdf-b302-053a-2704-ba5f74322625/mza_13119989780540450831.jpg/600x600bb.jpg"
        }
    ]
    
    # Remove old baseline mock songs from DB
    try:
        db.query(Song).filter(Song.id.like("song-%")).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Skipping deletion of old baseline songs: {e}")

    for s_data in baseline_songs:
        try:
            song = db.query(Song).filter(Song.id == s_data["id"]).first()
            if not song:
                new_song = Song(
                    id=s_data["id"],
                    spotify_id=s_data["spotify_id"],
                    title=s_data["title"],
                    artist=s_data["artist"],
                    album=s_data["album"],
                    duration=s_data["duration"],
                    image_url=s_data["image_url"]
                )
                db.add(new_song)
                db.commit()
            else:
                # Update metadata to ensure correctness
                song.title = s_data["title"]
                song.artist = s_data["artist"]
                song.album = s_data["album"]
                song.duration = s_data["duration"]
                song.image_url = s_data["image_url"]
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Skipping preload for song {s_data['id']} (likely handled by another worker): {e}")
    print("Baseline popular songs preloaded.")
