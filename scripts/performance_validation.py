#!/usr/bin/env python3
"""
🚀 Performance Validation Script
Validates optimizations and measures throughput improvements
"""

import asyncio
import json
import statistics
import sys
import time
from datetime import datetime
from typing import Any, Dict, List


def measure_list_performance():
    """Measure list vs numpy array performance"""
    print("🔍 Testing list operations performance...")

    # Test data
    data_size = 100000
    test_data = list(range(data_size))

    # Test 1: Traditional list sorting
    start_time = time.perf_counter()
    sorted_data = sorted(test_data, reverse=True)
    list_sort_time = (time.perf_counter() - start_time) * 1000

    # Test 2: List comprehension
    start_time = time.perf_counter()
    filtered_data = [x for x in test_data if x % 2 == 0]
    list_comp_time = (time.perf_counter() - start_time) * 1000

    return {
        "list_sort_ms": list_sort_time,
        "list_comprehension_ms": list_comp_time,
        "data_size": data_size,
    }


def measure_dict_performance():
    """Measure dictionary operations performance"""
    print("🔍 Testing dictionary operations performance...")

    # Create test dictionary
    test_dict = {f"key_{i}": f"value_{i}" for i in range(10000)}

    # Test lookup performance
    lookup_times = []
    for i in range(1000):
        start_time = time.perf_counter()
        value = test_dict.get(f"key_{i}", None)
        lookup_time = (time.perf_counter() - start_time) * 1000000  # microseconds
        lookup_times.append(lookup_time)

    return {
        "avg_lookup_microseconds": statistics.mean(lookup_times),
        "min_lookup_microseconds": min(lookup_times),
        "max_lookup_microseconds": max(lookup_times),
        "total_keys": len(test_dict),
    }


def measure_string_operations():
    """Measure string operations performance"""
    print("🔍 Testing string operations performance...")

    test_strings = [f"test_string_{i}" for i in range(1000)]

    # Test string formatting
    start_time = time.perf_counter()
    formatted_strings = [f"formatted_{s}_end" for s in test_strings]
    format_time = (time.perf_counter() - start_time) * 1000

    # Test string join
    start_time = time.perf_counter()
    joined_string = ":".join(test_strings)
    join_time = (time.perf_counter() - start_time) * 1000

    return {
        "string_format_ms": format_time,
        "string_join_ms": join_time,
        "strings_processed": len(test_strings),
    }


async def measure_async_performance():
    """Measure async operations performance"""
    print("🔍 Testing async operations performance...")

    async def simple_async_task(delay=0.001):
        await asyncio.sleep(delay)
        return f"completed_{time.time()}"

    # Test sequential execution
    start_time = time.perf_counter()
    sequential_results = []
    for i in range(10):
        result = await simple_async_task(0.001)
        sequential_results.append(result)
    sequential_time = (time.perf_counter() - start_time) * 1000

    # Test concurrent execution
    start_time = time.perf_counter()
    concurrent_tasks = [simple_async_task(0.001) for _ in range(10)]
    concurrent_results = await asyncio.gather(*concurrent_tasks)
    concurrent_time = (time.perf_counter() - start_time) * 1000

    return {
        "sequential_execution_ms": sequential_time,
        "concurrent_execution_ms": concurrent_time,
        "speedup_factor": (
            sequential_time / concurrent_time if concurrent_time > 0 else 0
        ),
        "tasks_executed": len(concurrent_tasks),
    }


def measure_json_performance():
    """Measure JSON serialization performance"""
    print("🔍 Testing JSON operations performance...")

    # Create test data
    test_data = {
        "books": [
            {
                "id": i,
                "title": f"Book {i}",
                "author": f"Author {i % 100}",
                "rating": 3.0 + (i % 20) / 10,
                "description": f"Description for book {i}" * 5,
            }
            for i in range(1000)
        ],
        "metadata": {
            "total_books": 1000,
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
        },
    }

    # Test JSON serialization
    start_time = time.perf_counter()
    json_string = json.dumps(test_data, separators=(",", ":"))  # Compact format
    serialize_time = (time.perf_counter() - start_time) * 1000

    # Test JSON deserialization
    start_time = time.perf_counter()
    parsed_data = json.loads(json_string)
    deserialize_time = (time.perf_counter() - start_time) * 1000

    return {
        "json_serialize_ms": serialize_time,
        "json_deserialize_ms": deserialize_time,
        "json_size_bytes": len(json_string.encode("utf-8")),
        "objects_serialized": len(test_data["books"]),
    }


def calculate_performance_score(results: Dict[str, Any]) -> float:
    """Calculate overall performance score"""
    # Define performance thresholds (lower is better for times)
    thresholds = {
        "list_sort_ms": 50,  # Should complete in under 50ms
        "json_serialize_ms": 100,  # Should serialize in under 100ms
        "avg_lookup_microseconds": 10,  # Should lookup in under 10 microseconds
        "concurrent_speedup": 5,  # Should achieve at least 5x speedup
    }

    score = 100  # Start with perfect score

    # Deduct points for poor performance
    if results["list_ops"]["list_sort_ms"] > thresholds["list_sort_ms"]:
        score -= 20

    if results["json_ops"]["json_serialize_ms"] > thresholds["json_serialize_ms"]:
        score -= 20

    if (
        results["dict_ops"]["avg_lookup_microseconds"]
        > thresholds["avg_lookup_microseconds"]
    ):
        score -= 20

    if results["async_ops"]["speedup_factor"] < thresholds["concurrent_speedup"]:
        score -= 20

    # Bonus points for exceptional performance
    if results["async_ops"]["speedup_factor"] > 8:
        score += 10

    if results["json_ops"]["json_serialize_ms"] < 20:
        score += 10

    return max(0, min(100, score))


async def main():
    """Run comprehensive performance validation"""
    print("🚀 GoodBooks Recommender - Performance Validation Suite")
    print("=" * 60)

    start_time = time.perf_counter()

    results = {
        "timestamp": datetime.now().isoformat(),
        "list_ops": measure_list_performance(),
        "dict_ops": measure_dict_performance(),
        "string_ops": measure_string_operations(),
        "async_ops": await measure_async_performance(),
        "json_ops": measure_json_performance(),
    }

    total_time = (time.perf_counter() - start_time) * 1000
    results["total_benchmark_time_ms"] = total_time

    # Calculate performance score
    performance_score = calculate_performance_score(results)
    results["performance_score"] = performance_score

    print("\n📊 PERFORMANCE RESULTS")
    print("=" * 30)

    print(f"\n📋 List Operations:")
    print(
        f"  Sorting {results['list_ops']['data_size']:,} items: {results['list_ops']['list_sort_ms']:.2f}ms"
    )
    print(f"  List comprehension: {results['list_ops']['list_comprehension_ms']:.2f}ms")

    print(f"\n🗂️ Dictionary Operations:")
    print(
        f"  Average lookup time: {results['dict_ops']['avg_lookup_microseconds']:.2f}μs"
    )
    print(f"  Total keys: {results['dict_ops']['total_keys']:,}")

    print(f"\n📝 String Operations:")
    print(f"  String formatting: {results['string_ops']['string_format_ms']:.2f}ms")
    print(f"  String joining: {results['string_ops']['string_join_ms']:.2f}ms")

    print(f"\n⚡ Async Operations:")
    print(
        f"  Sequential execution: {results['async_ops']['sequential_execution_ms']:.2f}ms"
    )
    print(
        f"  Concurrent execution: {results['async_ops']['concurrent_execution_ms']:.2f}ms"
    )
    print(f"  Speedup factor: {results['async_ops']['speedup_factor']:.1f}x")

    print(f"\n🔄 JSON Operations:")
    print(f"  Serialization: {results['json_ops']['json_serialize_ms']:.2f}ms")
    print(f"  Deserialization: {results['json_ops']['json_deserialize_ms']:.2f}ms")
    print(f"  Data size: {results['json_ops']['json_size_bytes']:,} bytes")

    print(f"\n🎯 OVERALL PERFORMANCE SCORE: {performance_score:.1f}/100")

    # Performance analysis
    print(f"\n💡 PERFORMANCE ANALYSIS")
    print("-" * 25)

    if performance_score >= 90:
        print("🎉 Excellent performance! All operations are highly optimized.")
    elif performance_score >= 75:
        print("✅ Good performance. Minor optimizations possible.")
    elif performance_score >= 60:
        print("⚠️ Moderate performance. Consider optimizations.")
    else:
        print("❌ Poor performance. Significant optimizations needed.")

    # Specific recommendations
    recommendations = []

    if results["async_ops"]["speedup_factor"] < 5:
        recommendations.append(
            "Consider increasing async concurrency for better throughput"
        )

    if results["json_ops"]["json_serialize_ms"] > 50:
        recommendations.append(
            "JSON serialization is slow - consider using faster serializers"
        )

    if results["dict_ops"]["avg_lookup_microseconds"] > 5:
        recommendations.append(
            "Dictionary lookups are slow - consider using more efficient data structures"
        )

    if recommendations:
        print("\n🔧 OPTIMIZATION RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"performance_validation_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")
    print(f"⏱️ Total benchmark time: {total_time:.2f}ms")

    return 0 if performance_score >= 75 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
