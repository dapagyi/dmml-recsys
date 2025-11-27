from litestar import Litestar, get, post
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from typing import List, Dict, Any
from src.recommenders import (
    ContentBasedRecommender,
    # TagBasedRecommender,
    # ItemBasedCF,
    # UserBasedCF,
    # PopularityRecommender,
)

from src.models import (
    ItemRecommendationRequest,
    RatingRecommendationRequest,
    RecommendationResponse,
    InitResponse,
)
from src.utils import load_data


def initialize_recommenders(app: Litestar) -> None:
    """Initialize all recommender systems"""
    ratings_df, movies_df = load_data()

    app.state.movies_df = movies_df
    app.state.ratings_df = ratings_df

    print("Initializing Content-Based Recommender...")
    app.state.content_based = ContentBasedRecommender(movies_df)

    # print("Initializing Tag-Based Recommender...")
    # app.state.tag_based = TagBasedRecommender(movies_df)

    # print("Initializing Item-Based CF...")
    # app.state.item_based_cf = ItemBasedCF(ratings_df)

    # print("Initializing User-Based CF...")
    # app.state.user_based_cf = UserBasedCF(ratings_df)

    # print("Initializing Popularity Recommender...")
    # app.state.popularity = PopularityRecommender(ratings_df)

    print("All recommenders initialized!")


@get("/api/init")
async def init_endpoint(state: State) -> InitResponse:
    """Return API information and available algorithms"""
    return InitResponse(
        dataset_url="/api/movies",
        algorithms={
            "item": [
                {
                    "id": "content_based",
                    "name": "Content-Based (Title + Genres)",
                    "endpoint": "/api/recommend/item/content",
                    "description": "Recommends items similar in content (genres, title) using TF-IDF and cosine similarity",
                },
                # {
                #     "id": "tag_based",
                #     "name": "Tag-Based (User Tags)",
                #     "endpoint": "/api/recommend/item/tags",
                #     "description": "Recommends items based on user-generated tags describing the movie content",
                # },
                # {
                #     "id": "item_cf",
                #     "name": "Item-Based Collaborative Filtering",
                #     "endpoint": "/api/recommend/item/cf",
                #     "description": "Recommends items that users who liked this item also liked",
                # },
            ],
            "rating": [
                # {
                #     "id": "user_cf",
                #     "name": "User-Based Collaborative Filtering",
                #     "endpoint": "/api/recommend/rating/cf",
                #     "description": "Recommends items based on similar users' preferences",
                # },
                # {
                #     "id": "popularity",
                #     "name": "Popularity-Based",
                #     "endpoint": "/api/recommend/rating/popularity",
                #     "description": "Recommends popular items (excluding already rated)",
                # },
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


@post("/api/recommend/item/tags")
async def recommend_tag_based(
    state: State, data: ItemRecommendationRequest
) -> RecommendationResponse:
    """Tag-based recommendations"""
    recommendations = state.tag_based.recommend(data.item_id, data.top_n)
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


cors_config = CORSConfig(
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    max_age=600,
)

app = Litestar(
    route_handlers=[
        init_endpoint,
        get_movies,
        recommend_content_based,
        recommend_tag_based,
        recommend_item_cf,
        recommend_user_cf,
        recommend_popularity,
    ],
    cors_config=cors_config,
    on_startup=[initialize_recommenders],
)
