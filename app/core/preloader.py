from sqlalchemy.orm import Session
from app.models.models import User, Song
from datetime import datetime

def preload_database(db: Session) -> None:
    # 1. Preload Default User
    try:
        default_user = db.query(User).filter(User.id == "default").first()
        if not default_user:
            new_user = User(
                id="default",
                name="Sharath",
                email="sharath@spotify.local",
                avatar=None,
                created_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            print("Default user preloaded.")
    except Exception as e:
        db.rollback()
        print(f"Skipping user preload (likely already exists or handled by another worker): {e}")

    # 2. Preload Hybrid Baseline Tracks (English, Hindi, and Telugu hits)
    baseline_songs = [
        # English
        {
            "id": "eng_1",
            "spotify_id": "7qiZRh2GesKMm28rRI5q66",
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "album": "Divide",
            "duration": "3:53",
            "image_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "eng_2",
            "spotify_id": "0V3wPSX3ygokj7v2EXj6v1",
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "duration": "3:20",
            "image_url": "https://images.unsplash.com/photo-1506157786151-b8491531f063?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "eng_3",
            "spotify_id": "4D7t7TTzfs2Rhw29ycu85X",
            "title": "As It Was",
            "artist": "Harry Styles",
            "album": "Harry's House",
            "duration": "2:47",
            "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "eng_4",
            "spotify_id": "5Pbee1XvhcZZpcse7JuLYA",
            "title": "Stay",
            "artist": "The Kid LAROI, Justin Bieber",
            "album": "F*CK LOVE 3: OVER YOU",
            "duration": "2:21",
            "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "eng_5",
            "spotify_id": "0y602COQ2dfHGHG3FFG5HG",
            "title": "Flowers",
            "artist": "Miley Cyrus",
            "album": "Endless Summer Vacation",
            "duration": "3:20",
            "image_url": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=300&auto=format&fit=crop&q=60"
        },
        # Hindi
        {
            "id": "hin_1",
            "spotify_id": "1tK4v94j5J137W4229ycuX",
            "title": "Tum Hi Ho",
            "artist": "Arijit Singh, Mithoon",
            "album": "Aashiqui 2",
            "duration": "4:22",
            "image_url": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "hin_2",
            "spotify_id": "4664v94j5J137W4229ycuY",
            "title": "Kesariya",
            "artist": "Arijit Singh, Pritam",
            "album": "Brahmastra",
            "duration": "4:28",
            "image_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "hin_3",
            "spotify_id": "7664v94j5J137W4229ycuZ",
            "title": "Apna Bana Le",
            "artist": "Arijit Singh, Sachin-Jigar",
            "album": "Bhediya",
            "duration": "4:21",
            "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "hin_4",
            "spotify_id": "8664v94j5J137W4229ycuW",
            "title": "Raataan Lambiyan",
            "artist": "Jubin Nautiyal, Asees Kaur",
            "album": "Shershaah",
            "duration": "3:50",
            "image_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "hin_5",
            "spotify_id": "9664v94j5J137W4229ycuV",
            "title": "Kabira",
            "artist": "Tochi Raina, Rekha Bhardwaj",
            "album": "Yeh Jawaani Hai Deewani",
            "duration": "4:11",
            "image_url": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=300&auto=format&fit=crop&q=60"
        },
        # Telugu
        {
            "id": "tel_1",
            "spotify_id": "0y74v94j5J137W4229ycuA",
            "title": "Naatu Naatu",
            "artist": "Rahul Sipligunj, Kaala Bhairava",
            "album": "RRR",
            "duration": "3:35",
            "image_url": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "tel_2",
            "spotify_id": "1y74v94j5J137W4229ycuB",
            "title": "Samajavaragamana",
            "artist": "Sid Sriram",
            "album": "Ala Vaikunthapurramuloo",
            "duration": "3:41",
            "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "tel_3",
            "spotify_id": "2y74v94j5J137W4229ycuC",
            "title": "Srivalli",
            "artist": "Sid Sriram",
            "album": "Pushpa: The Rise",
            "duration": "3:44",
            "image_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "tel_4",
            "spotify_id": "3y74v94j5J137W4229ycuD",
            "title": "Butta Bomma",
            "artist": "Armaan Malik",
            "album": "Ala Vaikunthapurramuloo",
            "duration": "3:17",
            "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&auto=format&fit=crop&q=60"
        },
        {
            "id": "tel_5",
            "spotify_id": "4y74v94j5J137W4229ycuE",
            "title": "Adiga Adiga",
            "artist": "Sid Sriram",
            "album": "Ninnu Kori",
            "duration": "3:46",
            "image_url": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&auto=format&fit=crop&q=60"
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
