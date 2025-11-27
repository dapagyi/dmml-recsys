from utils import load_data
from recommenders import (
    TagBasedRecommender,
)


def main():
    ratings_df, movies_df = load_data()
    # print("Ratings DataFrame:")
    # print(ratings_df.head())
    # print("\nMovies DataFrame:")
    # print(movies_df.head())

    recommender = TagBasedRecommender(movies_df)
    test_item_id = "1"  # Example movieId
    recommendations = recommender.recommend(test_item_id, top_n=5)
    print(
        f"Top 5 tag-based recommendations for item_id {test_item_id} ({movies_df.loc[movies_df['movieId'] == test_item_id, 'title'].values[0]}):"
    )
    for rec in recommendations:
        print(
            f"Item ID: {rec.item_id} ({movies_df.loc[movies_df['movieId'] == rec.item_id, 'title'].values[0]}), Score: {rec.score}"
        )


if __name__ == "__main__":
    main()
