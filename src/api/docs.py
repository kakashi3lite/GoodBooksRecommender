from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# Request Models
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = Field(
        None,
        description="User ID for personalized recommendations. If not provided, only content-based recommendations will be returned."
    )
    book_title: Optional[str] = Field(
        None,
        description="Book title to get similar recommendations. If not provided, only collaborative filtering recommendations will be returned."
    )
    n_recommendations: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Number of recommendations to return (min: 1, max: 20)"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": 12345,
                "book_title": "The Hobbit",
                "n_recommendations": 5
            }
        }

# Response Models
class BookRecommendation(BaseModel):
    book_id: int = Field(..., description="Unique identifier for the book")
    title: str = Field(..., description="Book title")
    authors: str = Field(..., description="Book authors")
    average_rating: float = Field(..., ge=0, le=5, description="Average rating (0-5)")
    similarity_score: float = Field(..., ge=0, le=1, description="Similarity score (0-1)")
    recommendation_type: str = Field(
        ...,
        description="Type of recommendation (content-based, collaborative, or hybrid)"
    )

    class Config:
        schema_extra = {
            "example": {
                "book_id": 1,
                "title": "The Lord of the Rings",
                "authors": "J.R.R. Tolkien",
                "average_rating": 4.5,
                "similarity_score": 0.95,
                "recommendation_type": "hybrid"
            }
        }

class RecommendationResponse(BaseModel):
    recommendations: List[BookRecommendation] = Field(
        ...,
        description="List of recommended books"
    )
    explanation: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Explanation of recommendations (e.g., similar tags, themes)"
    )

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "book_id": 1,
                        "title": "The Lord of the Rings",
                        "authors": "J.R.R. Tolkien",
                        "average_rating": 4.5,
                        "similarity_score": 0.95,
                        "recommendation_type": "hybrid"
                    }
                ],
                "explanation": {
                    "similar_tags": ["fantasy", "adventure", "magic"],
                    "similar_themes": ["epic journey", "good vs evil"]
                }
            }
        }

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "Book not found",
                "details": "The specified book title was not found in our database"
            }
        }

# API Documentation
API_DESCRIPTION = """
# GoodBooks Recommender API

This API provides book recommendations using a hybrid approach combining content-based and collaborative filtering.

## Features

* **Hybrid Recommendations**: Combines content-based similarity and collaborative filtering
* **Flexible Querying**: Get recommendations based on user ID, book title, or both
* **Detailed Results**: Includes book metadata, similarity scores, and recommendation explanations
* **Performance Optimized**: Uses caching and efficient similarity computations

## Authentication

This API uses API key authentication. Include your API key in the `X-API-Key` header.

## Rate Limiting

Requests are limited to:
* 100 requests per minute per API key
* 1000 requests per day per API key

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages when something goes wrong.

## Feedback

For issues, suggestions, or contributions, please visit our GitHub repository.
"""

# API Tags Metadata
API_TAGS_METADATA = [
    {
        "name": "recommendations",
        "description": "Operations for getting book recommendations"
    },
    {
        "name": "health",
        "description": "API health check endpoints"
    }
]

# Example Responses
EXAMPLE_RESPONSES = {
    404: {
        "model": ErrorResponse,
        "description": "Not Found",
        "content": {
            "application/json": {
                "example": {
                    "error": "Resource not found",
                    "details": "The requested resource could not be found"
                }
            }
        }
    },
    422: {
        "model": ErrorResponse,
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "error": "Validation error",
                    "details": "Invalid request parameters"
                }
            }
        }
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error": "Internal server error",
                    "details": "An unexpected error occurred"
                }
            }
        }
    }
}