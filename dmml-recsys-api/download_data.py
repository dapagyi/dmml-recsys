import os
import polars as pl
import urllib.request
import zipfile
from pathlib import Path


def download_movielens():
    """Download and extract MovieLens 100K dataset"""

    # Create data directory
    data_dir = Path("ml-latest-small")
    if data_dir.exists():
        print(f"Data directory {data_dir} already exists. Skipping download.")
        return

    # Download MovieLens 100K
    url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
    zip_path = "ml-latest-small.zip"

    print(f"Downloading MovieLens dataset from {url}...")
    urllib.request.urlretrieve(url, zip_path)

    print("Extracting files...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(".")

    # Clean up
    os.remove(zip_path)

    # Verify data
    ratings_df = pl.read_csv(data_dir / "ratings.csv")
    movies_df = pl.read_csv(data_dir / "movies.csv")

    print("\n" + "=" * 60)
    print("Data downloaded successfully!")
    print("=" * 60)
    print(f"\nRatings shape: {ratings_df.shape}")
    print(f"Movies shape: {movies_df.shape}")
    print(f"\nNumber of users: {ratings_df['userId'].n_unique()}")
    print(f"Number of movies: {movies_df['movieId'].n_unique()}")
    print(f"Number of ratings: {len(ratings_df)}")
    print("\nRating distribution:")
    print(ratings_df["rating"].value_counts().sort("rating"))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    download_movielens()
