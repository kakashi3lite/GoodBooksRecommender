from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.data.data_loader import DataLoader
from src.models.hybrid_recommender import HybridRecommender
import pandas as pd

app = FastAPI(
    title="GoodBooks Recommender API",
    description="A hybrid book recommendation system combining content-based and collaborative filtering",
    version="1.0.0"
)

# Initialize components
data_loader = DataLoader("data")
recommender = HybridRecommender()

# Load and prepare data
try:
    books, ratings, tags, book_tags = data_loader.load_datasets()
    merged_books = data_loader.merge_book_metadata(books, book_tags, tags)
    processed_books = data_loader.preprocess_tags(merged_books)
    recommender.fit(processed_books, ratings)
except Exception as e:
    print(f"Error initializing recommender: {str(e)}")

# Pydantic models for request/response
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    book_title: Optional[str] = None
    n_recommendations: Optional[int] = 5

class BookRecommendation(BaseModel):
    title: str
    authors: str
    average_rating: float
    hybrid_score: float

class RecommendationResponse(BaseModel):
    recommendations: List[BookRecommendation]
    explanation: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "GoodBooks Recommender API is running"}

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    try:
        if request.user_id is None and request.book_title is None:
            raise HTTPException(
                status_code=400,
                detail="Either user_id or book_title must be provided"
            )

        # Get recommendations
        recommendations = recommender.get_recommendations(
            user_id=request.user_id,
            book_title=request.book_title,
            n_recommendations=request.n_recommendations
        )

        # Get explanation if book title was provided
        explanation = None
        if request.book_title:
            explanation = recommender.explain_recommendations(request.book_title)

        # Convert recommendations to response format
        recommendation_list = [
            BookRecommendation(
                title=row['title'],
                authors=row['authors'],
                average_rating=row['average_rating'],
                hybrid_score=row['hybrid_score']
            )
            for _, row in recommendations.iterrows()
        ]

        return RecommendationResponse(
            recommendations=recommendation_list,
            explanation=explanation
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)