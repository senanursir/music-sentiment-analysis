import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline
import logging
from pathlib import Path
from typing import Optional
import warnings

warnings.filterwarnings("ignore")


class SentimentAnalyzer:
    def __init__(self, use_transformer: bool = True):
        self.vader = SentimentIntensityAnalyzer()
        self.logger = self._setup_logger()
        self.transformer_model = None
        if use_transformer:
            self._load_transformer()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("sentiment_analyzer")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            handler = logging.FileHandler("logs/sentiment_analyzer.log")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _load_transformer(self):
        try:
            self.transformer_model = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment",
                truncation=True,
                max_length=512,
            )
            self.logger.info("Transformer model yüklendi.")
        except Exception as e:
            self.logger.warning(f"Transformer yüklenemedi: {e}")
            self.transformer_model = None

    def vader_sentiment(self, text: str) -> dict:
        if not text or not isinstance(text, str):
            return {"vader_positive": None, "vader_negative": None, "vader_neutral": None, "vader_compound": None}
        scores = self.vader.polarity_scores(text)
        return {
            "vader_positive": scores["pos"],
            "vader_negative": scores["neg"],
            "vader_neutral": scores["neu"],
            "vader_compound": scores["compound"],
        }

    def textblob_sentiment(self, text: str) -> dict:
        if not text or not isinstance(text, str):
            return {"textblob_polarity": None, "textblob_subjectivity": None}
        blob = TextBlob(text)
        return {
            "textblob_polarity": blob.sentiment.polarity,
            "textblob_subjectivity": blob.sentiment.subjectivity,
        }

    def transformer_sentiment(self, text: str) -> dict:
        if not text or not isinstance(text, str) or self.transformer_model is None:
            return {"roberta_label": None, "roberta_score": None, "roberta_compound": None}
        try:
            truncated = text[:1024]
            result = self.transformer_model(truncated)[0]
            label = result["label"]
            score = result["score"]
            label_map = {"LABEL_0": -1, "LABEL_1": 0, "LABEL_2": 1}
            compound = label_map.get(label, 0) * score
            return {
                "roberta_label": label,
                "roberta_score": score,
                "roberta_compound": compound,
            }
        except Exception as e:
            self.logger.error(f"Transformer hatası: {e}")
            return {"roberta_label": None, "roberta_score": None, "roberta_compound": None}

    def analyze_text(self, text: str) -> dict:
        results = {}
        results.update(self.vader_sentiment(text))
        results.update(self.textblob_sentiment(text))
        if self.transformer_model:
            results.update(self.transformer_sentiment(text))
        return results

    def analyze_dataset(self, df: pd.DataFrame, lyrics_col: str = "lyrics") -> pd.DataFrame:
        result_df = df.copy()
        total = len(df)
        self.logger.info(f"{total} şarkı analiz ediliyor...")

        vader_results = []
        textblob_results = []
        roberta_results = []

        for idx, row in df.iterrows():
            lyrics = row.get(lyrics_col)
            has_lyrics = isinstance(lyrics, str) and len(lyrics.strip()) > 0

            text = lyrics if has_lyrics else None

            vader_results.append(self.vader_sentiment(text))
            textblob_results.append(self.textblob_sentiment(text))

            if self.transformer_model and has_lyrics:
                roberta_results.append(self.transformer_sentiment(text))
            else:
                roberta_results.append({"roberta_label": None, "roberta_score": None, "roberta_compound": None})

            if (idx + 1) % 50 == 0:
                print(f"  [{idx + 1}/{total}] işlendi...")

        vader_df = pd.DataFrame(vader_results)
        textblob_df = pd.DataFrame(textblob_results)
        roberta_df = pd.DataFrame(roberta_results)

        for col in vader_df.columns:
            result_df[col] = vader_df[col].values
        for col in textblob_df.columns:
            result_df[col] = textblob_df[col].values
        for col in roberta_df.columns:
            result_df[col] = roberta_df[col].values

        result_df = self._add_unified_sentiment(result_df)

        return result_df

    def _add_unified_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        scores = []
        for _, row in df.iterrows():
            available = []
            if pd.notna(row.get("vader_compound")):
                available.append(row["vader_compound"])
            if pd.notna(row.get("textblob_polarity")):
                available.append(row["textblob_polarity"])
            if pd.notna(row.get("roberta_compound")):
                available.append(row["roberta_compound"])
            scores.append(np.mean(available) if available else None)

        df["unified_sentiment"] = scores

        def classify(score):
            if score is None or np.isnan(score):
                return None
            if score >= 0.05:
                return "positive"
            elif score <= -0.05:
                return "negative"
            return "neutral"

        df["sentiment_label"] = df["unified_sentiment"].apply(classify)
        return df

    def compare_methods(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["vader_compound", "textblob_polarity"]
        if "roberta_compound" in df.columns:
            cols.append("roberta_compound")

        available = [c for c in cols if c in df.columns]
        valid = df[available].dropna()

        correlation = valid.corr()

        print("\n=== Yöntem Korelasyonları ===")
        print(correlation.round(3))

        print("\n=== Ortalama Sentiment Skorları ===")
        for col in available:
            mean_val = df[col].dropna().mean()
            std_val = df[col].dropna().std()
            print(f"  {col}: {mean_val:.4f} ± {std_val:.4f}")

        if "sentiment_label" in df.columns:
            print("\n=== Sentiment Dağılımı ===")
            dist = df["sentiment_label"].value_counts()
            total = dist.sum()
            for label, count in dist.items():
                print(f"  {label}: {count} ({count/total*100:.1f}%)")

        return correlation

    def get_statistics(self, df: pd.DataFrame) -> dict:
        stats = {
            "total_songs": len(df),
            "songs_with_lyrics": int(df["lyrics_found"].sum()) if "lyrics_found" in df.columns else None,
            "songs_analyzed": int(df["vader_compound"].notna().sum()) if "vader_compound" in df.columns else None,
        }

        for col in ["vader_compound", "textblob_polarity", "roberta_compound", "unified_sentiment"]:
            if col in df.columns:
                valid = df[col].dropna()
                stats[f"{col}_mean"] = round(float(valid.mean()), 4)
                stats[f"{col}_std"] = round(float(valid.std()), 4)

        return stats