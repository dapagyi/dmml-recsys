from pydantic import BaseModel
from typing import List, Dict, Any


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