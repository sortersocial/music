import os
from dotenv import load_dotenv
import json
import requests

# Add this line near the start of your code, before any env vars are used
load_dotenv()

def get_access_token():
    auth_url = "https://accounts.spotify.com/api/token"
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    print(client_id, client_secret)
    
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code == 200:
        return auth_response.json()['access_token']
    else:
        print(auth_response.json())
        raise Exception("Failed to get access token")

def spotify_api_call(endpoint, params=None):
    base_url = "https://api.spotify.com/v1"
    url = f"{base_url}{endpoint}"
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Spotify API call failed: {response.json()}")

# Search Spotify for album
def search_spotify(query):
    return spotify_api_call("/search", {"q": query, "type": "album", "limit": 1})

# Fetch album data
def fetch_album_data(album_id):
    return spotify_api_call(f"/albums/{album_id}")

# Sanitize names for file/directory paths
def sanitize_name(name):
    return ''.join(c if c.isalnum() or c in "- " else "" for c in name).replace(" ", "-").lower()

# Create directory if it doesn't exist
def create_directory(path):
    os.makedirs(path, exist_ok=True)

# Write JSON metadata to file
def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Add album, songs, and artist metadata
def add_album(album_data):
    artist_name = album_data["artists"][0]["name"]
    album_name = album_data["name"]
    sanitized_artist = sanitize_name(artist_name)
    sanitized_album = sanitize_name(album_name)
    
    # Define paths
    base_artist_dir = f"artists/{sanitized_artist}"
    album_dir = f"{base_artist_dir}/{sanitized_album}"
    
    # Create directories
    create_directory(album_dir)
    
    # Add album metadata - now one level higher with album name
    album_metadata = {
        "title": album_name,
        "artist": artist_name,
        "release_year": album_data["release_date"],
        "genres": album_data.get("genres", []),
        "tracklist": [track["id"] for track in album_data["tracks"]["items"]],
        "id": album_data["id"]
    }
    write_json(f"{base_artist_dir}/{sanitized_album}.json", album_metadata)
    print(f"Added album metadata to: {base_artist_dir}/{sanitized_album}.json")
    
    # Add songs metadata
    for track in album_data["tracks"]["items"]:
        sanitized_song = sanitize_name(track["name"])
        song_path = f"{album_dir}/{sanitized_song}.json"
        song_metadata = {
            "title": track["name"],
            "artist": artist_name,
            "album": album_name,
            "duration_ms": track["duration_ms"],
            "id": track["id"]
        }
        write_json(song_path, song_metadata)
        print(f"Added song metadata to: {song_path}")
    
    # Add artist metadata
    artist_metadata_path = f"{base_artist_dir}/metadata.json"
    if os.path.exists(artist_metadata_path):
        with open(artist_metadata_path, "r", encoding="utf-8") as f:
            artist_metadata = json.load(f)
        if album_name not in artist_metadata["albums"]:
            artist_metadata["albums"].append(album_name)
    else:
        artist_metadata = {
            "name": artist_name,
            "albums": [album_name],
            "id": album_data["artists"][0]["id"]
        }
    write_json(artist_metadata_path, artist_metadata)
    print(f"Added artist metadata to: {artist_metadata_path}")

# Main function to grab data
def grab(query):
    search_results = search_spotify(query)
    album = search_results["albums"]["items"][0]
    album_id = album["id"]
    album_data = fetch_album_data(album_id)
    add_album(album_data)

# CLI Entry Point
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3 or sys.argv[1] != "grab":
        print("Usage: python tool.py grab '<artist> - <album>'")
    else:
        query = sys.argv[2]
        grab(query)

