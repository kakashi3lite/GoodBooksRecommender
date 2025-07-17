#!/usr/bin/env python3
"""
🚀 GoodBooks Recommender - Performance Benchmarking Suite
Comprehensive performance testing and optimization validation
"""

import asyncio
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import aiohttp
import numpy as np
import pandas as pd
import psutil

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

try:
    from src.core.cache import AsyncCacheManager
    from src.core.settings import settings
    from src.models.hybrid_recommender import HybridRecommender
except ImportError:
    # Fallback for testing without full dependencies
    print("⚠️ Some modules not available - running limited benchmark")
    AsyncCacheManager = None
    HybridRecommender = None
    settings = None


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""

    operation: str
    duration_ms: float
    memory_mb: float
    cpu_percent: float
    throughput_ops_sec: float
    success: bool
    error: str = None


class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.baseline_metrics = {}

    def measure_resources(self) -> Tuple[float, float]:
        """Measure current memory and CPU usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        return memory_mb, cpu_percent

    async def benchmark_cache_operations(
        self, iterations: int = 1000
    ) -> List[BenchmarkResult]:
        """Benchmark cache get/set operations"""
        print(f"🔍 Benchmarking cache operations ({iterations} iterations)...")

        cache = AsyncCacheManager()
        await cache.initialize()

        results = []

        # Benchmark SET operations
        start_memory, start_cpu = self.measure_resources()
        start_time = time.perf_counter()

        for i in range(iterations):
            key = f"benchmark_key_{i}"
            value = {"data": f"test_value_{i}", "index": i, "timestamp": time.time()}
            success = await cache.set(key, value, ttl=300)

            if not success:
                results.append(
                    BenchmarkResult(
                        operation="cache_set",
                        duration_ms=0,
                        memory_mb=0,
                        cpu_percent=0,
                        throughput_ops_sec=0,
                        success=False,
                        error="Cache set failed",
                    )
                )

        end_time = time.perf_counter()
        end_memory, end_cpu = self.measure_resources()

        duration_ms = (end_time - start_time) * 1000
        throughput = iterations / (duration_ms / 1000)

        results.append(
            BenchmarkResult(
                operation="cache_set_batch",
                duration_ms=duration_ms,
                memory_mb=end_memory - start_memory,
                cpu_percent=end_cpu,
                throughput_ops_sec=throughput,
                success=True,
            )
        )

        # Benchmark GET operations
        start_memory, start_cpu = self.measure_resources()
        start_time = time.perf_counter()

        cache_hits = 0
        for i in range(iterations):
            key = f"benchmark_key_{i}"
            value = await cache.get(key)
            if value is not None:
                cache_hits += 1

        end_time = time.perf_counter()
        end_memory, end_cpu = self.measure_resources()

        duration_ms = (end_time - start_time) * 1000
        throughput = iterations / (duration_ms / 1000)

        results.append(
            BenchmarkResult(
                operation="cache_get_batch",
                duration_ms=duration_ms,
                memory_mb=end_memory - start_memory,
                cpu_percent=end_cpu,
                throughput_ops_sec=throughput,
                success=True,
            )
        )

        print(
            f"✅ Cache hit rate: {cache_hits}/{iterations} ({cache_hits/iterations*100:.1f}%)"
        )

        await cache.close()
        return results

    def benchmark_recommendation_engine(
        self, n_users: int = 100, n_books: int = 1000
    ) -> List[BenchmarkResult]:
        """Benchmark recommendation engine performance"""
        print(
            f"🤖 Benchmarking recommendation engine ({n_users} users, {n_books} books)..."
        )

        # Generate synthetic test data
        books_data = pd.DataFrame(
            {
                "book_id": range(1, n_books + 1),
                "title": [f"Book_{i}" for i in range(1, n_books + 1)],
                "authors": [f"Author_{i % 100}" for i in range(1, n_books + 1)],
                "average_rating": np.random.uniform(3.0, 5.0, n_books),
                "description": [
                    f"Description for book {i}" for i in range(1, n_books + 1)
                ],
            }
        )

        # Generate ratings data
        n_ratings = n_users * 20  # Average 20 ratings per user
        ratings_data = pd.DataFrame(
            {
                "user_id": np.random.randint(1, n_users + 1, n_ratings),
                "book_id": np.random.randint(1, n_books + 1, n_ratings),
                "rating": np.random.randint(1, 6, n_ratings),
            }
        ).drop_duplicates(subset=["user_id", "book_id"])

        results = []

        # Benchmark model training
        recommender = HybridRecommender()

        start_memory, start_cpu = self.measure_resources()
        start_time = time.perf_counter()

        try:
            recommender.fit(books_data, ratings_data)

            end_time = time.perf_counter()
            end_memory, end_cpu = self.measure_resources()

            training_duration = (end_time - start_time) * 1000

            results.append(
                BenchmarkResult(
                    operation="model_training",
                    duration_ms=training_duration,
                    memory_mb=end_memory - start_memory,
                    cpu_percent=end_cpu,
                    throughput_ops_sec=1000 / training_duration,  # Models per second
                    success=True,
                )
            )

            print(f"✅ Model training completed in {training_duration:.2f}ms")

        except Exception as e:
            results.append(
                BenchmarkResult(
                    operation="model_training",
                    duration_ms=0,
                    memory_mb=0,
                    cpu_percent=0,
                    throughput_ops_sec=0,
                    success=False,
                    error=str(e),
                )
            )
            return results

        # Benchmark prediction performance
        prediction_times = []
        successful_predictions = 0

        for user_id in range(1, min(51, n_users + 1)):  # Test first 50 users
            start_time = time.perf_counter()

            try:
                recommendations = recommender.get_recommendations(
                    user_id=user_id, n_recommendations=10
                )

                end_time = time.perf_counter()
                prediction_time = (end_time - start_time) * 1000
                prediction_times.append(prediction_time)
                successful_predictions += 1

            except Exception as e:
                print(f"⚠️ Prediction failed for user {user_id}: {e}")

        if prediction_times:
            avg_prediction_time = statistics.mean(prediction_times)
            p95_prediction_time = (
                statistics.quantiles(prediction_times, n=20)[18]
                if len(prediction_times) > 20
                else max(prediction_times)
            )
            throughput = 1000 / avg_prediction_time if avg_prediction_time > 0 else 0

            results.append(
                BenchmarkResult(
                    operation="recommendation_prediction",
                    duration_ms=avg_prediction_time,
                    memory_mb=0,  # Memory diff not measured for individual predictions
                    cpu_percent=0,
                    throughput_ops_sec=throughput,
                    success=True,
                )
            )

            print(f"✅ Average prediction time: {avg_prediction_time:.2f}ms")
            print(f"✅ 95th percentile: {p95_prediction_time:.2f}ms")
            print(f"✅ Throughput: {throughput:.1f} predictions/sec")

        return results

    async def benchmark_api_endpoints(
        self,
        base_url: str = "http://localhost:8000",
        concurrent_requests: int = 10,
        total_requests: int = 100,
    ) -> List[BenchmarkResult]:
        """Benchmark API endpoint performance"""
        print(
            f"🌐 Benchmarking API endpoints ({total_requests} requests, {concurrent_requests} concurrent)..."
        )

        results = []

        # Test data for requests
        test_payloads = [
            {"user_id": i % 100 + 1, "n_recommendations": 5}
            for i in range(total_requests)
        ]

        async def make_request(
            session: aiohttp.ClientSession, payload: dict
        ) -> Tuple[float, bool, str]:
            start_time = time.perf_counter()
            try:
                async with session.post(
                    f"{base_url}/recommendations",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    await response.json()
                    end_time = time.perf_counter()
                    return (end_time - start_time) * 1000, response.status == 200, ""
            except Exception as e:
                end_time = time.perf_counter()
                return (end_time - start_time) * 1000, False, str(e)

        # Run concurrent requests
        connector = aiohttp.TCPConnector(limit=concurrent_requests * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            semaphore = asyncio.Semaphore(concurrent_requests)

            async def limited_request(payload):
                async with semaphore:
                    return await make_request(session, payload)

            start_time = time.perf_counter()
            request_results = await asyncio.gather(
                *[limited_request(payload) for payload in test_payloads],
                return_exceptions=True,
            )
            end_time = time.perf_counter()

        # Analyze results
        successful_requests = []
        failed_requests = []

        for result in request_results:
            if isinstance(result, tuple):
                duration, success, error = result
                if success:
                    successful_requests.append(duration)
                else:
                    failed_requests.append((duration, error))

        if successful_requests:
            total_duration = (end_time - start_time) * 1000
            avg_response_time = statistics.mean(successful_requests)
            p95_response_time = (
                statistics.quantiles(successful_requests, n=20)[18]
                if len(successful_requests) > 20
                else max(successful_requests)
            )
            throughput = len(successful_requests) / (total_duration / 1000)

            results.append(
                BenchmarkResult(
                    operation="api_recommendations",
                    duration_ms=avg_response_time,
                    memory_mb=0,
                    cpu_percent=0,
                    throughput_ops_sec=throughput,
                    success=True,
                )
            )

            print(
                f"✅ Successful requests: {len(successful_requests)}/{total_requests}"
            )
            print(f"✅ Average response time: {avg_response_time:.2f}ms")
            print(f"✅ 95th percentile: {p95_response_time:.2f}ms")
            print(f"✅ Throughput: {throughput:.1f} req/sec")

        if failed_requests:
            print(f"❌ Failed requests: {len(failed_requests)}")

        return results

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.results:
            return {"error": "No benchmark results available"}

        # Group results by operation
        operations = {}
        for result in self.results:
            if result.operation not in operations:
                operations[result.operation] = []
            operations[result.operation].append(result)

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "operations": {},
            "recommendations": [],
        }

        total_successful = sum(1 for r in self.results if r.success)
        total_failed = len(self.results) - total_successful

        report["summary"] = {
            "total_operations": len(self.results),
            "successful": total_successful,
            "failed": total_failed,
            "success_rate": total_successful / len(self.results) * 100,
        }

        # Analyze each operation type
        for op_name, op_results in operations.items():
            successful_results = [r for r in op_results if r.success]

            if successful_results:
                durations = [r.duration_ms for r in successful_results]
                throughputs = [r.throughput_ops_sec for r in successful_results]

                report["operations"][op_name] = {
                    "count": len(successful_results),
                    "avg_duration_ms": statistics.mean(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "avg_throughput_ops_sec": (
                        statistics.mean(throughputs) if throughputs else 0
                    ),
                    "success_rate": len(successful_results) / len(op_results) * 100,
                }

        # Generate performance recommendations
        recommendations = []

        # Check cache performance
        if "cache_get_batch" in report["operations"]:
            cache_throughput = report["operations"]["cache_get_batch"][
                "avg_throughput_ops_sec"
            ]
            if cache_throughput < 1000:
                recommendations.append(
                    "Consider optimizing cache operations - throughput below 1000 ops/sec"
                )

        # Check API performance
        if "api_recommendations" in report["operations"]:
            api_duration = report["operations"]["api_recommendations"][
                "avg_duration_ms"
            ]
            if api_duration > 200:
                recommendations.append(
                    "API response time above 200ms - consider optimization"
                )

        # Check model performance
        if "recommendation_prediction" in report["operations"]:
            pred_duration = report["operations"]["recommendation_prediction"][
                "avg_duration_ms"
            ]
            if pred_duration > 100:
                recommendations.append(
                    "Model prediction time above 100ms - consider model optimization"
                )

        report["recommendations"] = recommendations

        return report


async def main():
    """Run comprehensive performance benchmarks"""
    print("🚀 Starting GoodBooks Recommender Performance Benchmark Suite")
    print("=" * 60)

    benchmark = PerformanceBenchmark()

    try:
        # Benchmark 1: Cache Operations
        cache_results = await benchmark.benchmark_cache_operations(iterations=500)
        benchmark.results.extend(cache_results)

        print()

        # Benchmark 2: Recommendation Engine
        model_results = benchmark.benchmark_recommendation_engine(
            n_users=50, n_books=500
        )
        benchmark.results.extend(model_results)

        print()

        # Benchmark 3: API Endpoints (if server is running)
        try:
            api_results = await benchmark.benchmark_api_endpoints(
                concurrent_requests=5, total_requests=50
            )
            benchmark.results.extend(api_results)
        except Exception as e:
            print(f"⚠️ API benchmarks skipped - server may not be running: {e}")

        print()
        print("=" * 60)
        print("📊 Generating Performance Report...")

        # Generate and save report
        report = benchmark.generate_performance_report()

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_benchmark_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Performance report saved to: {report_file}")

        # Print summary
        print("\n📈 PERFORMANCE SUMMARY")
        print("-" * 30)
        print(f"Total Operations: {report['summary']['total_operations']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")

        for op_name, op_data in report["operations"].items():
            print(f"\n{op_name.upper()}")
            print(f"  Average Duration: {op_data['avg_duration_ms']:.2f}ms")
            print(f"  Throughput: {op_data['avg_throughput_ops_sec']:.1f} ops/sec")

        if report["recommendations"]:
            print("\n💡 OPTIMIZATION RECOMMENDATIONS")
            print("-" * 35)
            for rec in report["recommendations"]:
                print(f"• {rec}")
        else:
            print("\n🎉 All performance metrics are within acceptable ranges!")

    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
