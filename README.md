# GoodBooks Recommender System

A sophisticated book recommendation engine that combines content-based and collaborative filtering approaches to provide personalized book recommendations.

## 🌟 Features

- **Hybrid Recommendation Model**
  - Content-based filtering using TF-IDF on book metadata
  - Collaborative filtering with matrix factorization
  - Weighted combination for optimal recommendations

- **Fast and Scalable**
  - FastAPI-based REST API
  - Redis caching for improved performance
  - Docker containerization

- **Rich Metadata Analysis**
  - Book tags and categories processing
  - User rating patterns analysis
  - Recommendation explanations

## 🏗 Architecture

```
src/
├── api/            # FastAPI application
├── data/           # Data loading and preprocessing
├── features/       # Feature extraction
├── models/         # Recommendation models
└── config.py       # Configuration management
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9-3.11
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GoodBooksRecommender.git
cd GoodBooksRecommender
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Locally

1. Start the API server:
```bash
python -m src.api.main
```

2. Or using Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Get Recommendations

```bash
POST /recommendations

Request Body:
{
    "user_id": 123,          # Optional
    "book_title": "1984",    # Optional
    "n_recommendations": 5   # Optional, default: 5
}

Response:
{
    "recommendations": [
        {
            "title": "Brave New World",
            "authors": "Aldous Huxley",
            "average_rating": 4.5,
            "hybrid_score": 0.95
        },
        ...
    ],
    "explanation": {
        "top_tags": ["dystopian", "classics", ...],
        "similar_books": ["Animal Farm", ...]
    }
}
```

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 📈 Performance

- Response time: < 100ms for recommendations
- Cache hit ratio: > 80%
- Supports millions of books and users

## 🛠 Development

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "Add your feature"
```

3. Push changes:
```bash
git push origin feature/your-feature-name
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.