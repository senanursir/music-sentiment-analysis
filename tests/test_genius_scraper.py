import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.genius_scraper import GeniusLyricsScraper


def test_single_song():
    """Single song test"""

    scraper = GeniusLyricsScraper()

    # Test songs
    test_songs = [
        ("The Beatles", "Hey Jude"),
        ("Queen", "Bohemian Rhapsody"),
        ("Ed Sheeran", "Shape of You")
    ]

    for artist, track in test_songs:
        print(f"\n Searching: {artist} - {track}")
        lyrics = scraper.search_song_lyrics(artist, track)

        if lyrics:
            print(f"({len(lyrics)} characters)")
            print(f" {lyrics[:100]}...")
        else:
            print("Not found")


def test_dataset_sample():
    """Test with dataset sample"""

    # Create sample data
    sample_data = pd.DataFrame({
        'Artist': ['The Beatles', 'Queen', 'Bob Dylan'],
        'Track': ['Hey Jude', 'Bohemian Rhapsody', 'Like a Rolling Stone'],
        'Year': [1968, 1975, 1965]
    })

    scraper = GeniusLyricsScraper()
    result = scraper.process_dataset(sample_data, batch_size=3, delay=2)


    stats = scraper.get_statistics(result)
    print(f"Success rate: {stats['success_rate']:.1f}%")

    return result


if __name__ == "__main__":
    test_single_song()
    test_dataset_sample()