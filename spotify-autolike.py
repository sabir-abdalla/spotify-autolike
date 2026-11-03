import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
SCOPE = "playlist-read-private user-library-modify user-library-read"

if not all([CLIENT_ID, CLIENT_SECRET, PLAYLIST_ID]):
    raise SystemExit(
        "Missing credentials. Copy .env.example to .env and fill in the values."
    )

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotify_cache",
))

def get_all_playlist_tracks(playlist_id):
    print(f"Fetching tracks from playlist...")
    tracks = []
    results = sp.playlist_items(playlist_id, additional_types=["track"], limit=100)
    
    while results:
        for item in results["items"]:
            if not item: continue
            track = item.get("track") or item.get("item")
            if track and track.get("id"):
                tracks.append(track)
        results = sp.next(results) if results.get("next") else None
    return tracks

def clear_liked_songs():
    print("Clearing existing Liked Songs to ensure a fresh start...")
    results = sp.current_user_saved_tracks(limit=50)
    count = 0
    
    while results and results['items']:
        for item in results['items']:
            if item['track']:
                uri = item['track']['uri']
                try:
                    sp._delete("me/library", uris=uri)
                    count += 1
                    if count % 10 == 0:
                        print(f"  Removed {count} songs...")
                except Exception as e:
                    print(f"  X Failed to remove: {e}")
                
                time.sleep(0.8) 
        
        results = sp.current_user_saved_tracks(limit=50)
        time.sleep(1)
    
    print(f"Library cleared ({count} songs removed).\n")

def like_in_descending_order(playlist_id):
    clear_liked_songs()
    tracks = get_all_playlist_tracks(playlist_id)
    
    if not tracks:
        print("No valid Spotify tracks found in playlist.")
        return

    tracks_bottom_up = list(reversed(tracks))
    print(f"Found {len(tracks_bottom_up)} tracks. Liking bottom -> top...\n")

    for i, track in enumerate(tracks_bottom_up, 1):
        uri = track["uri"]
        try:
            sp.current_user_saved_tracks_add(tracks=[uri])
            artist = ", ".join(a["name"] for a in track["artists"])
            print(f"  [{i}/{len(tracks_bottom_up)}] O Liked: {track['name']} — {artist}")
        except Exception as e:
            print(f"  X Failed: {track['name']} ({e})")

        time.sleep(0.8) 

    print(f"\nDone! The playlist is now in your Liked Songs.")

if __name__ == "__main__":
    like_in_descending_order(PLAYLIST_ID)