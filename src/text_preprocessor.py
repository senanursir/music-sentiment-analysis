import re
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from langdetect import detect, LangDetectException


class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('text_preprocessor')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            handler = logging.FileHandler('logs/text_preprocessor.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def clean_lyrics(self, lyrics: str) -> Optional[str]:
        if not lyrics or not isinstance(lyrics, str):
            return None

        text = re.sub(r'\[.*?\]', '', lyrics)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) < 50:
            return None

        return text

    def detect_language(self, text: str) -> Optional[str]:
        try:
            return detect(text)
        except LangDetectException:
            return None

    def is_english(self, text: str) -> bool:
        lang = self.detect_language(text)
        return lang == 'en'

    def tokenize_and_lemmatize(self, text: str) -> list:
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t.isalpha()]
        tokens = [t for t in tokens if t not in self.stop_words]
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        return tokens

    def process_single(self, lyrics: str) -> dict:
        result = {
            'cleaned_lyrics': None,
            'language': None,
            'is_english': False,
            'tokens': None,
            'token_count': 0
        }

        cleaned = self.clean_lyrics(lyrics)
        if not cleaned:
            return result

        result['cleaned_lyrics'] = cleaned
        lang = self.detect_language(cleaned)
        result['language'] = lang
        result['is_english'] = lang == 'en'

        if result['is_english']:
            tokens = self.tokenize_and_lemmatize(cleaned)
            result['tokens'] = tokens
            result['token_count'] = len(tokens)

        return result

    def process_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        result_df = df.copy()

        result_df['cleaned_lyrics'] = None
        result_df['language'] = None
        result_df['is_english'] = False
        result_df['tokens'] = None
        result_df['token_count'] = 0

        total = len(df)
        self.logger.info(f"Processing {total} songs...")

        for idx, row in df.iterrows():
            lyrics = row.get('lyrics')

            if pd.isna(lyrics) or not lyrics:
                continue

            processed = self.process_single(str(lyrics))

            result_df.at[idx, 'cleaned_lyrics'] = processed['cleaned_lyrics']
            result_df.at[idx, 'language'] = processed['language']
            result_df.at[idx, 'is_english'] = processed['is_english']
            result_df.at[idx, 'tokens'] = str(processed['tokens']) if processed['tokens'] else None
            result_df.at[idx, 'token_count'] = processed['token_count']

            if (idx + 1) % 50 == 0:
                print(f"[{idx + 1}/{total}] işlendi")

        return result_df

    def get_statistics(self, df: pd.DataFrame) -> dict:
        total = len(df)

        has_lyrics = df['cleaned_lyrics'].notna().sum()

        english_songs = df['is_english'].sum() if 'is_english' in df.columns else 0
        avg_tokens = df['token_count'].mean() if 'token_count' in df.columns else 0

        return {
            'total_songs': total,
            'has_lyrics': int(has_lyrics),
            'english_songs': int(english_songs),
            'non_english_filtered': int(has_lyrics) - int(english_songs),
            'avg_token_count': round(avg_tokens, 1)
        }









