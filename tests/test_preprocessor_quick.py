import pandas as pd
from src.text_preprocessor import TextPreprocessor

preprocessor = TextPreprocessor()

test_lyrics = "Yeah breakfast at Tiffanys and bottles of bubbles girls with tattoos who like getting in trouble"
result = preprocessor.process_single(test_lyrics)

print("Cleaned:", result['cleaned_lyrics'])
print("Language:", result['language'])
print("English:", result['is_english'])
print("Tokens:", result['tokens'][:10])
print("Token Count:", result['token_count'])
