from typing import List
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import RecommendationOutput


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
