from tests.test_api_client import test_spotify_connection, test_genius_connection

if __name__ == "__main__":
    test_spotify_connection()
    test_genius_connection()

    import pandas as pd
    from pathlib import Path
    from src.genius_scraper import GeniusLyricsScraper


    def collect_lyrics():
        """Main lyrics collection function"""

        # Load the dataset
        dataset_path = "data/raw/Hot100.csv"
        print(f"{dataset_path}")

        if not Path(dataset_path).exists():
            print(f" Dataset not found: {dataset_path}")
            return

        df = pd.read_csv(dataset_path)
        print(f" Loaded {len(df)} songs")
        print(f"Columns: {list(df.columns)}")

        # Initialize scraper
        scraper = GeniusLyricsScraper()


        # First test - with 5 songs
        test_df = df.head(5).copy()

        result_df = scraper.process_dataset(
            df=test_df,
            batch_size=5,
            delay=2.0  # Slower for testing
        )

        # Save results
        output_path = Path("data/processed/test_results.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)

        # Statistics
        stats = scraper.get_statistics(result_df)
        print(f"\n Test Results:")
        print(f"Total songs: {stats['total_songs']}")
        print(f"Lyrics found: {stats['lyrics_found']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")

        # Successful ones
        successful = result_df[result_df['lyrics_found'] == True]
        print(f"\n Successfully found lyrics for:")
        for _, row in successful.iterrows():
            print(f"   • {row['Artist']} - {row['Track']}")



        choice = input("\nProcess the full dataset? (y/n): ")
        if choice.lower() == 'y':
            full_result = scraper.process_dataset(
                df=df,
                batch_size=100,
                delay=1.5
            )

            full_output = Path("data/processed/billboard_with_lyrics.csv")
            full_result.to_csv(full_output, index=False)

            final_stats = scraper.get_statistics(full_result)
            print(f"\nStats:")
            print(f"Total songs: {final_stats['total_songs']}")
            print(f"Lyrics found: {final_stats['lyrics_found']}")
            print(f"Success rate: {final_stats['success_rate']:.1f}%")


    if __name__ == "__main__":
        collect_lyrics()