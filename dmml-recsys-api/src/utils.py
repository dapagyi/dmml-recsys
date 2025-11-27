import pandas as pd
from pathlib import Path
import re

def load_data():
    """Load MovieLens data"""
    data_dir = Path("ml-latest-small")

    ratings_df = pd.read_csv(data_dir / "ratings.csv")
    movies_df = pd.read_csv(data_dir / "movies.csv")

    # Extract year from title
    movies_df["year"] = movies_df["title"].str.extract(r"\((\d{4})\)$")

    # Remove year from title
    movies_df["title"] = movies_df["title"].str.replace(
        r"\s*\(\d{4}\)$", "", regex=True
    )

    # Fix title parsing - handle articles at the end
    def fix_title(title):
        if pd.isna(title):
            return title
        match = re.match(r"^(.+),\s+(A|An|The)$", title)
        if match:
            return f"{match.group(2)} {match.group(1)}"
        return title

    movies_df["title"] = movies_df["title"].apply(fix_title)

    # Convert movieId to string BEFORE merging
    movies_df["movieId"] = movies_df["movieId"].astype(str)
    ratings_df["movieId"] = ratings_df["movieId"].astype(str)

    # Load tags
    tags_file = data_dir / "tags.csv"
    if tags_file.exists():
        tags_df = pd.read_csv(tags_file)
        tags_df["movieId"] = tags_df["movieId"].astype(str)
        movie_tags = (
            tags_df.groupby("movieId")["tag"].apply(lambda x: " ".join(x)).reset_index()
        )
        movies_df = movies_df.merge(movie_tags, on="movieId", how="left")
        movies_df["tag"] = movies_df["tag"].fillna("")
    else:
        movies_df["tag"] = ""

    return ratings_df, movies_df