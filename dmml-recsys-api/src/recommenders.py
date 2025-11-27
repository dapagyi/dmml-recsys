from typing import List
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from src.models import RecommendationOutput, RatingInput

class ContentBasedRecommender:
    """TF-IDF based content recommendation using title and genres"""

    def __init__(self, movies_df: pd.DataFrame):
        self.movies_df = movies_df
        self.tfidf_matrix = None
        self.cosine_sim = None
        self._preprocess()

    def _preprocess(self):
        self.movies_df["content"] = (
            self.movies_df["title"] + " " + self.movies_df["genres"].fillna("")
        )

        tfidf = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = tfidf.fit_transform(self.movies_df["content"])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def recommend(self, item_id: str, top_n: int = 10) -> List[RecommendationOutput]:
        try:
            idx = self.movies_df[self.movies_df["movieId"] == item_id].index[0]
        except IndexError:
            return []

        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1 : top_n + 1]

        recommendations = []
        for idx, score in sim_scores:
            recommendations.append(
                RecommendationOutput(
                    item_id=self.movies_df.iloc[idx]["movieId"], score=float(score)
                )
            )

        return recommendations


class TagBasedRecommender:
    """TF-IDF based on user tags"""

    def __init__(self, movies_df: pd.DataFrame):
        self.movies_df = movies_df
        self.tfidf_matrix = None
        self.cosine_sim = None
        self._preprocess()

    def _preprocess(self):
        content = self.movies_df["tag"].fillna("")

        tfidf = TfidfVectorizer(stop_words="english", min_df=1, max_df=0.8)
        self.tfidf_matrix = tfidf.fit_transform(content)
        self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def recommend(self, item_id: str, top_n: int = 10) -> List[RecommendationOutput]:
        try:
            idx = self.movies_df[self.movies_df["movieId"] == item_id].index[0]
        except IndexError:
            return []

        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1 : top_n + 1]

        recommendations = []
        for idx, score in sim_scores:
            if score > 0:
                recommendations.append(
                    RecommendationOutput(
                        item_id=self.movies_df.iloc[idx]["movieId"], score=float(score)
                    )
                )

        return recommendations


class ItemBasedCF:
    """Item-Item Collaborative Filtering"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.item_similarity_df = None
        self._preprocess()

    def _preprocess(self):
        item_user_matrix = self.ratings_df.pivot_table(
            index="movieId", columns="userId", values="rating"
        ).fillna(0)

        item_similarity = cosine_similarity(item_user_matrix)
        self.item_similarity_df = pd.DataFrame(
            item_similarity,
            index=item_user_matrix.index,
            columns=item_user_matrix.index,
        )

    def recommend(self, item_id: str, top_n: int = 10) -> List[RecommendationOutput]:
        if item_id not in self.item_similarity_df.index:
            return []

        sim_scores = self.item_similarity_df[item_id].sort_values(ascending=False)
        sim_scores = sim_scores[1 : top_n + 1]

        recommendations = []
        for movie_id, score in sim_scores.items():
            recommendations.append(
                RecommendationOutput(item_id=movie_id, score=float(score))
            )

        return recommendations


class UserBasedCF:
    """User-User Collaborative Filtering"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.user_item_matrix = None
        self._preprocess()

    def _preprocess(self):
        self.user_item_matrix = self.ratings_df.pivot_table(
            index="userId", columns="movieId", values="rating"
        ).fillna(0)

    def recommend_from_ratings(
        self, ratings: List[RatingInput], top_n: int = 10
    ) -> List[RecommendationOutput]:
        user_vector = pd.Series(0, index=self.user_item_matrix.columns)
        for rating in ratings:
            if rating.item_id in user_vector.index:
                user_vector[rating.item_id] = rating.rating

        similarities = []
        for idx, row in self.user_item_matrix.iterrows():
            sim = self._cosine_similarity(user_vector, row)
            if sim > 0:
                similarities.append((idx, sim))

        if not similarities:
            return []

        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:50]

        recommendations = defaultdict(float)
        total_sim = defaultdict(float)
        rated_items = {r.item_id for r in ratings}

        for user_id, sim in similarities:
            user_ratings = self.user_item_matrix.loc[user_id]
            for item_id, rating in user_ratings[user_ratings > 0].items():
                if item_id not in rated_items:
                    recommendations[item_id] += rating * sim
                    total_sim[item_id] += sim

        for item_id in recommendations:
            if total_sim[item_id] > 0:
                recommendations[item_id] /= total_sim[item_id]

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


class PopularityRecommender:
    """Simple popularity-based recommender"""

    def __init__(self, ratings_df: pd.DataFrame):
        self.ratings_df = ratings_df
        self.popular_items = None
        self._preprocess()

    def _preprocess(self):
        item_stats = (
            self.ratings_df.groupby("movieId")
            .agg({"rating": ["mean", "count"]})
            .reset_index()
        )
        item_stats.columns = ["movieId", "avg_rating", "count"]

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
