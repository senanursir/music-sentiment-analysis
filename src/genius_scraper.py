import pandas as pd
import lyricsgenius
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict
import os
import sys
import re

# import congif file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GENIUS_ACCESS_TOKEN


class GeniusLyricsScraper:
    def __init__(self):
        """Class that fetches song lyrics using the Genius API"""
        self.genius = self._setup_genius_api()
        self.logger = self._setup_logger()


    def _setup_genius_api(self) -> lyricsgenius.Genius:
        """configure the Genius API"""
        genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
        genius.verbose = False
        genius.remove_section_headers = True
        genius.skip_non_songs = True
        genius.excluded_terms = ["(Remix)", "(Live)", "(Acoustic)"]

        return genius


    def _setup_logger(self) -> logging.Logger:
        """Logger setup"""
        logger = logging.getLogger('genius_scraper')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # make log directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            handler = logging.FileHandler('logs/genius_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger


    def search_song_lyrics(self, artist: str, track: str) -> Optional[str]:
        """the lyrics of a single song"""
        try:
            # Clear track name
            clean_track = self._clean_track_name(track)
            clean_artist = self._clean_artist_name(artist)

            song = self.genius.search_song(clean_track, clean_artist)

            if song and song.lyrics:
                # Clear lyrics
                cleaned_lyrics = self._clean_lyrics(song.lyrics)
                self.logger.info(f"Found: {artist} - {track}")
                return cleaned_lyrics
            else:
                self.logger.warning(f"Not found: {artist} - {track}")
                return None

        except Exception as e:
            self.logger.error(f"Error processing {artist} - {track}: {str(e)}")
            return None


    def _clean_track_name(self, track: str) -> str:
        """Clear rack name"""
        track = re.sub(r'\([^)]*\)', '', track).strip()
        track = re.sub(r'\[[^\]]*\]', '', track).strip()
        return track


    def _clean_artist_name(self, artist: str) -> str:
        """Clear artist name"""
        artist = re.split(r'\bfeat\.|\bft\.|\bfeaturing\b', artist, flags=re.IGNORECASE)[0]
        return artist.strip()


    def _clean_lyrics(self, lyrics: str) -> str:
        """Clean 'Lyrics' '"""
        if not lyrics:
            return None

        lyrics = lyrics.replace('\\n', '\n')
        lines = lyrics.split('\n')

        # delete first row which is begins w 'Lyrics'
        if lines and 'Lyrics' in lines[0]:
            lines = lines[1:]

        # delete the part containing ‘Embed’ or ‘You might also like’ in the last line
        if lines and any(word in lines[-1] for word in ['Embed', 'You might also like']):
            lines = lines[:-1]

        return '\n'.join(lines).strip()


    def process_dataset(self,
                        df: pd.DataFrame,
                        batch_size: int = 100,
                        delay: float = 1.0,
                        start_idx: int = 0) -> pd.DataFrame:

        results_df = df.copy()
        if 'lyrics' not in results_df.columns:
            results_df['lyrics'] = None
        if 'lyrics_found' not in results_df.columns:
            results_df['lyrics_found'] = False

        total_songs = len(df)
        end_idx = min(start_idx + batch_size, total_songs)

        self.logger.info(f"Processing songs {start_idx}-{end_idx} of {total_songs}")

        for idx in range(start_idx, end_idx):
            row = df.iloc[idx]
            artist = row['Artist']
            track = row['Track']

            print(f"[{idx + 1}/{total_songs}] Processing: {artist} - {track}")

            lyrics = self.search_song_lyrics(artist, track)

            results_df.at[idx, 'lyrics'] = lyrics
            results_df.at[idx, 'lyrics_found'] = lyrics is not None

            time.sleep(delay)

            # save a backup per 25 songs.
            if (idx + 1) % 25 == 0:
                self._save_backup(results_df.loc[:idx], f"backup_{start_idx}_{idx}.csv")

        return results_df


    def _save_backup(self, df: pd.DataFrame, filename: str):
        """For backup"""
        # create new data/processed directory
        backup_path = Path("data/processed")
        backup_path.mkdir(parents=True, exist_ok=True)

        full_path = backup_path / filename
        df.to_csv(full_path, index=False)
        self.logger.info(f"Backup saved: {filename}")


    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """statistics"""
        total = len(df)
        found = df['lyrics_found'].sum() if 'lyrics_found' in df.columns else 0
        not_found = total - found

        return {
            'total_songs': total,
            'lyrics_found': found,
            'lyrics_not_found': not_found,
            'success_rate': (found / total * 100) if total > 0 else 0
        }