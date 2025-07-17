#!/usr/bin/env python
"""
AI Recommendation Testing Script
Chain-of-Thought: Verify AI recommendations with real data and performance metrics
Memory: Track performance over time for optimization
Forward-Thinking: Test various recommendation strategies for quality
"""

import requests
import json
import time
import argparse
import sys
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

# Configuration
DEFAULT_API_URL = "http://localhost:8000"
RECOMMENDATION_ENDPOINT = "/api/books/recommend"
PERFORMANCE_METRICS_FILE = "recommendation_performance.json"
RESULTS_DIR = "test_results"

# Ensure results directory exists
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test AI book recommendations")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--strategy", choices=["collaborative", "content", "hybrid", "neural"], 
                      default="hybrid", help="Recommendation strategy to test")
    parser.add_argument("--limit", type=int, default=20, help="Number of recommendations to fetch")
    parser.add_argument("--genre", action="append", help="Filter by genre (can be used multiple times)")
    parser.add_argument("--user-id", help="Test for specific user ID")
    parser.add_argument("--plot", action="store_true", help="Generate performance plots")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    return parser.parse_args()

def fetch_recommendations(args):
    """Fetch recommendations from API with performance metrics"""
    url = f"{args.api_url}{RECOMMENDATION_ENDPOINT}"
    
    params = {
        "strategy": args.strategy,
        "limit": args.limit
    }
    
    if args.user_id:
        params["user_id"] = args.user_id
        
    if args.genre:
        params["genres"] = ",".join(args.genre)
    
    print(f"\n🔍 Fetching recommendations with strategy: {args.strategy}")
    print(f"   URL: {url}")
    print(f"   Parameters: {params}\n")
    
    # Measure API response time
    start_time = time.time()
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        api_latency = time.time() - start_time
        
        # Parse recommendations
        recommendations = response.json()
        
        # Successful response
        print(f"✅ API returned {len(recommendations)} recommendations")
        print(f"   Response time: {api_latency:.2f}s\n")
        
        return {
            "success": True,
            "recommendations": recommendations,
            "count": len(recommendations),
            "api_latency": api_latency,
            "timestamp": datetime.now().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        api_latency = time.time() - start_time
        print(f"❌ API request failed: {e}")
        print(f"   Response time: {api_latency:.2f}s\n")
        
        return {
            "success": False,
            "error": str(e),
            "api_latency": api_latency,
            "timestamp": datetime.now().isoformat()
        }

def analyze_recommendations(recommendations, args):
    """Analyze recommendation quality and performance"""
    if not recommendations.get("success"):
        print("⚠️ Cannot analyze recommendations: API request failed")
        return recommendations
    
    recs = recommendations["recommendations"]
    
    # Basic stats
    ratings = [book.get("rating", 0) for book in recs]
    avg_rating = np.mean(ratings) if ratings else 0
    
    # AI scores
    ai_scores = [book.get("ai_recommendation_score", 0) for book in recs]
    avg_ai_score = np.mean(ai_scores) if ai_scores else 0
    
    # Genre diversity
    all_genres = []
    for book in recs:
        all_genres.extend(book.get("genres", []))
    
    unique_genres = set(all_genres)
    genre_counts = {genre: all_genres.count(genre) for genre in unique_genres}
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    top_genres = sorted_genres[:5] if sorted_genres else []
    
    # Authors diversity
    authors = [book.get("authors", "Unknown") for book in recs]
    unique_authors = set(authors)
    
    # Years diversity
    years = [book.get("published_year", 0) for book in recs]
    year_range = max(years) - min(years) if years and min(years) > 0 else 0
    
    # Store analysis results
    analysis = {
        "avg_rating": avg_rating,
        "avg_ai_score": avg_ai_score,
        "unique_genres": len(unique_genres),
        "unique_authors": len(unique_authors),
        "year_range": year_range,
        "top_genres": top_genres,
        "genre_diversity_score": len(unique_genres) / len(all_genres) if all_genres else 0,
        "author_diversity_score": len(unique_authors) / len(authors) if authors else 0
    }
    
    recommendations["analysis"] = analysis
    
    # Print analysis
    print("\n📊 Recommendation Analysis:")
    print(f"   Average Rating: {avg_rating:.2f}/5.0")
    print(f"   Average AI Score: {avg_ai_score:.2f}")
    print(f"   Genre Diversity: {len(unique_genres)} unique genres")
    print(f"   Author Diversity: {len(unique_authors)} unique authors")
    print(f"   Publication Year Range: {year_range} years")
    
    print("\n📚 Top Genres:")
    for genre, count in top_genres:
        print(f"   - {genre}: {count}")
    
    if args.verbose:
        print("\n📖 Book Details:")
        for i, book in enumerate(recs[:10]):  # Show first 10 books in verbose mode
            print(f"\n   {i+1}. {book.get('title', 'Unknown')} ({book.get('published_year', 'Unknown')})")
            print(f"      Author: {book.get('authors', 'Unknown')}")
            print(f"      Rating: {book.get('rating', 'Unknown')}/5.0")
            print(f"      AI Score: {book.get('ai_recommendation_score', 'Unknown')}")
            print(f"      Genres: {', '.join(book.get('genres', []))}")
            if book.get('ai_explanation'):
                print(f"      AI Explanation: {book.get('ai_explanation')}")
    
    return recommendations

def save_performance_metrics(results):
    """Save performance metrics to file"""
    # Load existing metrics if available
    metrics = []
    if os.path.exists(PERFORMANCE_METRICS_FILE):
        try:
            with open(PERFORMANCE_METRICS_FILE, 'r') as f:
                metrics = json.load(f)
        except json.JSONDecodeError:
            metrics = []
    
    # Add new metrics
    metrics.append({
        "timestamp": results.get("timestamp"),
        "strategy": results.get("strategy"),
        "api_latency": results.get("api_latency"),
        "success": results.get("success"),
        "count": results.get("count", 0)
    })
    
    # Save metrics
    with open(PERFORMANCE_METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Save detailed results
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"{RESULTS_DIR}/ai_recommendation_test_{timestamp_str}.json"
    
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {result_file}")
    print(f"   Performance metrics updated in {PERFORMANCE_METRICS_FILE}")

def generate_plots(args):
    """Generate performance plots from saved metrics"""
    if not os.path.exists(PERFORMANCE_METRICS_FILE):
        print("⚠️ No performance metrics found for plotting")
        return
    
    # Load metrics
    with open(PERFORMANCE_METRICS_FILE, 'r') as f:
        metrics = json.load(f)
    
    if not metrics:
        print("⚠️ No metrics data available for plotting")
        return
    
    # Extract data for plotting
    timestamps = []
    latencies = []
    strategies = []
    
    for metric in metrics:
        if metric.get("success", False):
            timestamps.append(datetime.fromisoformat(metric.get("timestamp")))
            latencies.append(metric.get("api_latency", 0))
            strategies.append(metric.get("strategy", "unknown"))
    
    if not timestamps:
        print("⚠️ No successful API calls found for plotting")
        return
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    # Plot by strategy
    unique_strategies = set(strategies)
    for strategy in unique_strategies:
        strategy_indices = [i for i, s in enumerate(strategies) if s == strategy]
        strategy_timestamps = [timestamps[i] for i in strategy_indices]
        strategy_latencies = [latencies[i] for i in strategy_indices]
        
        plt.plot(strategy_timestamps, strategy_latencies, 'o-', label=strategy)
    
    plt.title('API Latency Over Time by Strategy')
    plt.xlabel('Timestamp')
    plt.ylabel('Latency (seconds)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis to show dates nicely
    plt.gcf().autofmt_xdate()
    
    # Save plot
    plot_file = f"{RESULTS_DIR}/ai_recommendation_performance.png"
    plt.savefig(plot_file)
    print(f"\n📈 Performance plot saved to {plot_file}")

def main():
    """Main test function"""
    args = parse_arguments()
    
    print("\n🤖 AI Book Recommendation Test")
    print("=" * 40)
    
    if args.plot:
        generate_plots(args)
        return
    
    # Fetch recommendations
    results = fetch_recommendations(args)
    
    # Add test parameters to results
    results["strategy"] = args.strategy
    results["limit"] = args.limit
    results["genres"] = args.genre
    results["user_id"] = args.user_id
    
    # Analyze recommendations
    if results.get("success"):
        results = analyze_recommendations(results, args)
    
    # Save metrics
    save_performance_metrics(results)
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    main()
