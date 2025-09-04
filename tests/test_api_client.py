from src.api_client import get_genius_client, get_spotify_clients


def test_spotify_connection():
    """
    Creates and returns Spotify API client.
    :return: spotipy.Spotify: Spotify client object.
    """
    sp = get_spotify_clients()

    try:
        results = sp.search(q='The Box Roddy Ricch', type='track', limit=1)
        assert len(results['tracks']['items']) > 0

        track = results['tracks']['items'][0]
        print(f"🎵 Test song: {track['name']} - {track['artists'][0]['name']}")
        print("✅ Spotify API is working!")
        return True

    except AssertionError:
        print("❌ The song could not be found! The API is working but there are no results.")
        return False

    except Exception as e:
        print(f"❌ Spotify API connection test failed: {e}")
        return False


def test_genius_connection():
    """

    :return:
    """
    genius = get_genius_client()
    try:
        song = genius.search_song("The Box", "Roddy Ricch")
        assert song is not None, "Song not found. There may be a problem with the Genius API connection."

        print(f"🎤 Test song: {song.title} - {song.artist}")
        print("✅ Genius API is working!")
        return True

    except AssertionError as e:
        print(f"❌ Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Genius API connection test failed: {e}")
        return False


if __name__ == "__main__":
    test_spotify_connection()
    test_genius_connection()
