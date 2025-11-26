"""
Recommendation Systems Workshop API

Setup:
1. Install dependencies:
   uv pip install litestar uvicorn pandas numpy scikit-learn

2. Download MovieLens data (run once):
   python download_data.py

3. Run the API:
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

# main.py
from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict


# ============================================================================
# DATA MODELS
# ============================================================================


class ItemRecommendationRequest(BaseModel):
    item_id: str
    top_n: int = 10


class RatingInput(BaseModel):
    item_id: str
    rating: float


class RatingRecommendationRequest(BaseModel):
    ratings: List[RatingInput]
    top_n: int = 10


class RecommendationOutput(BaseModel):
    item_id: str
    score: float


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationOutput]


class InitResponse(BaseModel):
    dataset_url: str
    algorithms: Dict[str, List[Dict[str, Any]]]


# ============================================================================
# RECOMMENDATION ALGORITHMS
# ============================================================================


class ContentBasedRecommender:
    """TF-IDF based content recommendation"""

    def __init__(self, movies_df: pd.DataFrame):
        self.movies_df = movies_df
        self.tfidf_matrix = None
        self.cosine_sim = None
        self._preprocess()

    def _preprocess(self):
        # Combine title and genres for content
        self.movies_df["content"] = (
            self.movies_df["title"] + " " + self.movies_df["genres"].fillna("")
        )

        # Calculate TF-IDF
        tfidf = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = tfidf.fit_transform(self.movies_df["content"])

        # Calculate cosine similarity
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def recommend(self, item_id: str, top_n: int = 10) -> List[RecommendationOutput]:
        try:
            idx = self.movies_df[self.movies_df["movieId"] == item_id].index[0]
        except IndexError:
            return []

        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1 : top_n + 1]  # Exclude the item itself

        movie_indices = [i[0] for i in sim_scores]
        scores = [i[1] for i in sim_scores]

        recommendations = []
        for idx, score in zip(movie_indices, scores):
            recommendations.append(
                RecommendationOutput(
                    item_id=self.movies_df.iloc[idx]["movieId"], score=float(score)
                )
            )

        return recommendations


class CollaborativeFilteringRecommender:
    """User-User Collaborative Filtering"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.user_item_matrix = None
        self.item_user_matrix = None
        self._preprocess()

    def _preprocess(self):
        # Create user-item matrix
        self.user_item_matrix = self.ratings_df.pivot_table(
            index="userId", columns="movieId", values="rating"
        ).fillna(0)

        self.item_user_matrix = self.user_item_matrix.T

    def recommend_from_ratings(
        self, ratings: List[RatingInput], top_n: int = 10
    ) -> List[RecommendationOutput]:
        # Create a vector for the input user
        user_vector = pd.Series(0, index=self.user_item_matrix.columns)
        for rating in ratings:
            if rating.item_id in user_vector.index:
                user_vector[rating.item_id] = rating.rating

        # Calculate similarity with all users
        similarities = []
        for idx, row in self.user_item_matrix.iterrows():
            sim = self._cosine_similarity(user_vector, row)
            if sim > 0:
                similarities.append((idx, sim))

        if not similarities:
            return []

        # Get top similar users
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:50]

        # Aggregate ratings from similar users
        recommendations = defaultdict(float)
        total_sim = defaultdict(float)

        rated_items = {r.item_id for r in ratings}

        for user_id, sim in similarities:
            user_ratings = self.user_item_matrix.loc[user_id]
            for item_id, rating in user_ratings[user_ratings > 0].items():
                if item_id not in rated_items:
                    recommendations[item_id] += rating * sim
                    total_sim[item_id] += sim

        # Calculate weighted average
        for item_id in recommendations:
            if total_sim[item_id] > 0:
                recommendations[item_id] /= total_sim[item_id]

        # Sort and return top N
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[
            :top_n
        ]

        return [
            RecommendationOutput(item_id=item_id, score=float(score))
            for item_id, score in sorted_recs
        ]

    def _cosine_similarity(self, vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)


class ItemBasedCF:
    """Item-Item Collaborative Filtering"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.item_similarity = None
        self._preprocess()

    def _preprocess(self):
        # Create item-user matrix
        item_user_matrix = self.ratings_df.pivot_table(
            index="movieId", columns="userId", values="rating"
        ).fillna(0)

        # Calculate item-item similarity
        self.item_similarity = cosine_similarity(item_user_matrix)
        self.item_similarity_df = pd.DataFrame(
            self.item_similarity,
            index=item_user_matrix.index,
            columns=item_user_matrix.index,
        )

    def recommend(self, item_id: str, top_n: int = 10) -> List[RecommendationOutput]:
        if item_id not in self.item_similarity_df.index:
            return []

        # Get similar items
        sim_scores = self.item_similarity_df[item_id].sort_values(ascending=False)
        sim_scores = sim_scores[1 : top_n + 1]  # Exclude the item itself

        recommendations = []
        for movie_id, score in sim_scores.items():
            recommendations.append(
                RecommendationOutput(item_id=movie_id, score=float(score))
            )

        return recommendations


class PopularityRecommender:
    """Simple popularity-based recommender"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.popular_items = None
        self._preprocess()

    def _preprocess(self):
        # Calculate popularity score (average rating * number of ratings)
        item_stats = (
            self.ratings_df.groupby("movieId")
            .agg({"rating": ["mean", "count"]})
            .reset_index()
        )
        item_stats.columns = ["movieId", "avg_rating", "count"]

        # Weighted score
        item_stats["score"] = item_stats["avg_rating"] * np.log1p(item_stats["count"])
        self.popular_items = item_stats.sort_values("score", ascending=False)

    def recommend(
        self, top_n: int = 10, exclude_items: List[str] = None
    ) -> List[RecommendationOutput]:
        if exclude_items:
            items = self.popular_items[
                ~self.popular_items["movieId"].isin(exclude_items)
            ]
        else:
            items = self.popular_items

        items = items.head(top_n)

        recommendations = []
        for _, row in items.iterrows():
            recommendations.append(
                RecommendationOutput(item_id=row["movieId"], score=float(row["score"]))
            )

        return recommendations

    def recommend_from_ratings(
        self, ratings: List[RatingInput], top_n: int = 10
    ) -> List[RecommendationOutput]:
        rated_items = [r.item_id for r in ratings]
        return self.recommend(top_n, exclude_items=rated_items)


# ============================================================================
# DATA LOADING
# ============================================================================


def load_data():
    """Load MovieLens data"""
    data_dir = Path("ml-latest-small")

    # Load ratings
    ratings_df = pd.read_csv(data_dir / "ratings.csv")

    # Load movies
    movies_df = pd.read_csv(data_dir / "movies.csv")

    # Extract year from title
    movies_df["year"] = movies_df["title"].str.extract(r"\((\d{4})\)$")
    movies_df["title"] = movies_df["title"].str.replace(
        r"\s*\(\d{4}\)$", "", regex=True
    )

    # Convert movieId to string for consistency
    movies_df["movieId"] = movies_df["movieId"].astype(str)
    ratings_df["movieId"] = ratings_df["movieId"].astype(str)

    return ratings_df, movies_df


def initialize_recommenders(app: Litestar) -> None:
    """Initialize all recommender systems"""
    ratings_df, movies_df = load_data()

    app.state.movies_df = movies_df
    app.state.ratings_df = ratings_df

    # Initialize recommenders
    print("Initializing Content-Based Recommender...")
    app.state.content_based = ContentBasedRecommender(movies_df)

    print("Initializing Item-Based CF...")
    app.state.item_based_cf = ItemBasedCF(ratings_df)

    print("Initializing User-Based CF...")
    app.state.user_based_cf = CollaborativeFilteringRecommender(ratings_df)

    print("Initializing Popularity Recommender...")
    app.state.popularity = PopularityRecommender(ratings_df)

    print("All recommenders initialized!")


# ============================================================================
# API ENDPOINTS
# ============================================================================


@get("/api/init")
async def init_endpoint(state: State) -> InitResponse:
    """Return API information and available algorithms"""
    return InitResponse(
        dataset_url="/api/movies",
        algorithms={
            "item": [
                {
                    "id": "content_based",
                    "name": "Content-Based (TF-IDF)",
                    "endpoint": "/api/recommend/item/content",
                    "description": "Recommends items similar in content (genres, title) using TF-IDF and cosine similarity",
                },
                {
                    "id": "item_cf",
                    "name": "Item-Based Collaborative Filtering",
                    "endpoint": "/api/recommend/item/cf",
                    "description": "Recommends items that users who liked this item also liked",
                },
            ],
            "rating": [
                {
                    "id": "user_cf",
                    "name": "User-Based Collaborative Filtering",
                    "endpoint": "/api/recommend/rating/cf",
                    "description": "Recommends items based on similar users' preferences",
                },
                {
                    "id": "popularity",
                    "name": "Popularity-Based",
                    "endpoint": "/api/recommend/rating/popularity",
                    "description": "Recommends popular items (excluding already rated)",
                },
            ],
        },
    )


@get("/api/movies")
async def get_movies(state: State) -> List[Dict[str, Any]]:
    """Return list of movies for frontend"""
    movies = state.movies_df[["movieId", "title", "year"]].to_dict("records")
    return movies


@post("/api/recommend/item/content")
async def recommend_content_based(
    state: State, data: ItemRecommendationRequest
) -> RecommendationResponse:
    """Content-based recommendations"""
    recommendations = state.content_based.recommend(data.item_id, data.top_n)
    return RecommendationResponse(recommendations=recommendations)


@post("/api/recommend/item/cf")
async def recommend_item_cf(
    state: State, data: ItemRecommendationRequest
) -> RecommendationResponse:
    """Item-based collaborative filtering recommendations"""
    recommendations = state.item_based_cf.recommend(data.item_id, data.top_n)
    return RecommendationResponse(recommendations=recommendations)


@post("/api/recommend/rating/cf")
async def recommend_user_cf(
    state: State, data: RatingRecommendationRequest
) -> RecommendationResponse:
    """User-based collaborative filtering recommendations"""
    recommendations = state.user_based_cf.recommend_from_ratings(
        data.ratings, data.top_n
    )
    return RecommendationResponse(recommendations=recommendations)


@post("/api/recommend/rating/popularity")
async def recommend_popularity(
    state: State, data: RatingRecommendationRequest
) -> RecommendationResponse:
    """Popularity-based recommendations"""
    recommendations = state.popularity.recommend_from_ratings(data.ratings, data.top_n)
    return RecommendationResponse(recommendations=recommendations)


# ============================================================================
# APP CONFIGURATION
# ============================================================================

cors_config = CORSConfig(
    allow_origins=[
        "*",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app = Litestar(
    route_handlers=[
        init_endpoint,
        get_movies,
        recommend_content_based,
        recommend_item_cf,
        recommend_user_cf,
        recommend_popularity,
    ],
    cors_config=cors_config,
    on_startup=[initialize_recommenders],
)
