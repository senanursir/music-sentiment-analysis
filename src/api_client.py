import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GENIUS_ACCESS_TOKEN

def get_spotify_clients():
    client_credentials_manager = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_genius_client():
    return lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout=30, verbose=False)
