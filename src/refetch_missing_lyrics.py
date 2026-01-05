import lyricsgenius
import pandas as pd
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import GENIUS_ACCESS_TOKEN

genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
genius.verbose = False
genius.remove_section_headers = True
genius.skip_non_songs = True
genius.excluded_terms = ["(Remix)", "(Live)"]


def get_lyrics_safe(artist, track, max_retries=3):
    for attempt in range(max_retries):
        try:
            song = genius.search_song(track, artist)

            if song and song.lyrics:
                return song.lyrics.strip()
            else:
                return None

        except Exception as e:
            print(f"    Error ( {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None


def fetch_missing_lyrics(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    print({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    print(f"Rows: {len(df)}")

    invalid_mask = df['lyrics'].isnull() | (df['lyrics'] == '') | (df['lyrics'] == 'False')
    missing_indices = df[invalid_mask].index.tolist()

    print(f"missing: {len(missing_indices)}")
    print(f"validlyrics: {len(df) - len(missing_indices)}")

    if len(missing_indices) == 0:
        print("\n All lyrics are here")
        return

    proceed = input(f"\n{len(missing_indices)}  lyrics? (y/n): ")
    if proceed.lower() != 'y':
        return

    success_count = 0
    fail_count = 0


    for i, idx in enumerate(missing_indices, 1):
        track = df.at[idx, 'Track']
        artist = df.at[idx, 'Artist']

        print(f"[{i}/{len(missing_indices)}] {artist} - {track}")

        lyrics = get_lyrics_safe(artist, track)

        if lyrics:
            df.at[idx, 'lyrics'] = lyrics
            success_count += 1
            print(f"  Succsessful: ({len(lyrics)} )")
        else:
            fail_count += 1
            print(f" Unsuccessful ")

        if i % 10 == 0:
            df.to_csv(output_csv, index=False)
            print(f"\n   {success_count} succ, {fail_count} not\n")

        time.sleep(1)

    df.to_csv(output_csv, index=False)


    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Successful {success_count}")
    print(f"Unuccessful {fail_count}")
    print(f"Rate {success_count / (success_count + fail_count) * 100:.1f}%")
    print(f"Saved {output_csv}")

    final_valid = df['lyrics'].notna() & (df['lyrics'] != '') & (df['lyrics'] != 'False')
    print(f"Total songs: {len(df)}")
    print(f"Valid lyrics: {final_valid.sum()} ({final_valid.sum() / len(df) * 100:.1f}%)")



if __name__ == "__main__":
    input_file = '../data/processed/billboard_with_lyrics.csv'
    output_file = '../data/processed/billboard_with_lyrics_v2.csv'

    fetch_missing_lyrics(input_file, output_file)