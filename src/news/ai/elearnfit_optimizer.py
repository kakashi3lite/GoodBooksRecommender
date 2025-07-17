"""
E-LearnFit Small Model Optimization System
Efficient Learning and Fitting for lightweight AI models
COT: Large LMs are expensive—what if smaller models can perform just as well?
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import numpy as np

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle
from src.news.ai.scorerag_summarization import ScoreRAGSummary

logger = StructuredLogger(__name__)


class ModelSize(Enum):
    """Available model sizes for E-LearnFit optimization"""
    LARGE = "claude-3-5-sonnet-20241022"     # Reference model
    MEDIUM = "claude-3-haiku-20240307"       # Medium model
    SMALL_QWEN = "qwen1.5-7b-chat"          # Small efficient model
    SMALL_SOLAR = "solar-10.7b-instruct"    # Alternative small model
    TINY_LLAMA = "tinyllama-1.1b-chat"      # Ultra-lightweight


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for model comparison"""
    
    model_name: str
    accuracy_score: float         # 0-1, factual accuracy
    speed_ms: float              # Response time in milliseconds
    cost_per_request: float      # Estimated cost
    quality_score: float         # Overall quality rating
    factual_consistency: float   # Consistency with reference
    efficiency_ratio: float      # Quality/cost ratio
    benchmark_passed: bool       # Meets minimum thresholds


@dataclass
class ELearnFitResult:
    """E-LearnFit optimization result"""
    
    recommended_model: str
    performance_comparison: Dict[str, ModelPerformanceMetrics]
    cost_savings_percent: float
    quality_maintained: bool
    fallback_strategy: str
    optimization_reasoning: str


class ELearnFitOptimizer:
    """
    COT: Benchmark & optionally swap GPT-4 for small models using E-LearnFit
    
    Research Integration: E-LearnFit techniques for model efficiency
    - Benchmark multiple model sizes on news summarization tasks
    - Compare accuracy, speed, and cost metrics
    - Dynamically select optimal model for workload
    - Maintain quality thresholds with cost optimization
    """

    def __init__(self):
        self.session = None
        
        # E-LearnFit parameters
        self.accuracy_threshold = 0.85      # Minimum accuracy to maintain
        self.speed_threshold_ms = 500       # Maximum response time
        self.cost_optimization_target = 0.7 # Target cost reduction
        
        # Benchmark test cases for evaluation
        self.benchmark_articles = self._create_benchmark_dataset()
        
        # Model configuration
        self.model_configs = {
            ModelSize.LARGE: {
                "api_base": "https://api.anthropic.com/v1/messages",
                "cost_per_token": 0.00003,  # Estimated
                "expected_quality": 0.95
            },
            ModelSize.MEDIUM: {
                "api_base": "https://api.anthropic.com/v1/messages", 
                "cost_per_token": 0.00001,
                "expected_quality": 0.88
            },
            ModelSize.SMALL_QWEN: {
                "api_base": "http://localhost:8001/v1/chat/completions",  # Local inference
                "cost_per_token": 0.000001,
                "expected_quality": 0.82
            },
            ModelSize.SMALL_SOLAR: {
                "api_base": "http://localhost:8002/v1/chat/completions",
                "cost_per_token": 0.000002,
                "expected_quality": 0.85
            },
            ModelSize.TINY_LLAMA: {
                "api_base": "http://localhost:8003/v1/chat/completions",
                "cost_per_token": 0.0000001,
                "expected_quality": 0.75
            }
        }

    async def __aenter__(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def optimize_model_selection(
        self,
        task_type: str = "news_summarization",
        quality_priority: bool = False
    ) -> ELearnFitResult:
        """
        COT: Run E-LearnFit optimization to find optimal model
        
        Process:
        1. Benchmark all available models on test cases
        2. Compare accuracy, speed, and cost metrics
        3. Calculate efficiency ratios
        4. Select optimal model based on constraints
        """
        try:
            logger.info("Starting E-LearnFit model optimization", task_type=task_type)
            
            # Stage 1: Benchmark Models
            performance_results = await self._benchmark_all_models()
            
            # Stage 2: Calculate Efficiency Ratios
            efficiency_results = self._calculate_efficiency_ratios(performance_results)
            
            # Stage 3: Select Optimal Model
            optimal_model = self._select_optimal_model(
                efficiency_results, quality_priority
            )
            
            # Stage 4: Generate Optimization Report
            result = self._generate_optimization_result(
                optimal_model, efficiency_results
            )

            logger.info(
                "E-LearnFit optimization complete",
                recommended_model=result.recommended_model,
                cost_savings=result.cost_savings_percent
            )

            return result

        except Exception as e:
            logger.error("E-LearnFit optimization failed", error=str(e))
            raise

    async def _benchmark_all_models(self) -> Dict[str, ModelPerformanceMetrics]:
        """
        COT: Benchmark all models on standardized test cases
        Measure accuracy, speed, cost for fair comparison
        """
        results = {}
        
        for model_size in ModelSize:
            logger.info(f"Benchmarking model: {model_size.value}")
            
            try:
                # Run benchmark tasks
                metrics = await self._benchmark_single_model(model_size)
                results[model_size.value] = metrics
                
            except Exception as e:
                logger.warning(f"Benchmark failed for {model_size.value}", error=str(e))
                # Create default metrics for failed models
                results[model_size.value] = ModelPerformanceMetrics(
                    model_name=model_size.value,
                    accuracy_score=0.0,
                    speed_ms=float('inf'),
                    cost_per_request=float('inf'),
                    quality_score=0.0,
                    factual_consistency=0.0,
                    efficiency_ratio=0.0,
                    benchmark_passed=False
                )

        return results

    async def _benchmark_single_model(self, model_size: ModelSize) -> ModelPerformanceMetrics:
        """
        COT: Benchmark individual model on test cases
        Run multiple tasks and aggregate performance metrics
        """
        config = self.model_configs[model_size]
        
        # Metrics accumulation
        total_accuracy = 0.0
        total_speed = 0.0
        total_cost = 0.0
        total_quality = 0.0
        successful_runs = 0
        
        # Run benchmark on test articles
        for i, test_article in enumerate(self.benchmark_articles[:3]):  # Top 3 for speed
            try:
                start_time = time.time()
                
                # Generate summary using model
                summary = await self._generate_summary_with_model(
                    model_size, test_article
                )
                
                end_time = time.time()
                
                # Calculate metrics
                speed_ms = (end_time - start_time) * 1000
                accuracy = self._evaluate_summary_accuracy(test_article, summary)
                quality = self._evaluate_summary_quality(summary)
                cost = self._estimate_request_cost(config, summary)
                
                total_accuracy += accuracy
                total_speed += speed_ms
                total_cost += cost
                total_quality += quality
                successful_runs += 1
                
            except Exception as e:
                logger.warning(f"Benchmark task {i} failed for {model_size.value}", error=str(e))
                continue

        if successful_runs == 0:
            raise Exception(f"All benchmark tasks failed for {model_size.value}")

        # Calculate averages
        avg_accuracy = total_accuracy / successful_runs
        avg_speed = total_speed / successful_runs
        avg_cost = total_cost / successful_runs
        avg_quality = total_quality / successful_runs
        
        # Calculate consistency (simplified)
        consistency = self._calculate_factual_consistency(model_size)
        
        # Check if benchmark passed
        benchmark_passed = (
            avg_accuracy >= self.accuracy_threshold and
            avg_speed <= self.speed_threshold_ms
        )

        return ModelPerformanceMetrics(
            model_name=model_size.value,
            accuracy_score=avg_accuracy,
            speed_ms=avg_speed,
            cost_per_request=avg_cost,
            quality_score=avg_quality,
            factual_consistency=consistency,
            efficiency_ratio=0.0,  # Will be calculated later
            benchmark_passed=benchmark_passed
        )

    async def _generate_summary_with_model(
        self, 
        model_size: ModelSize, 
        article: NewsArticle
    ) -> str:
        """
        COT: Generate summary using specific model
        Standardized prompt for fair comparison
        """
        config = self.model_configs[model_size]
        
        # Standardized summarization prompt
        prompt = f"""
        Summarize this news article in 2-3 clear, factual sentences:

        Title: {article.title}
        Content: {article.content[:1000]}

        Summary (50-100 words):
        """

        try:
            if model_size in [ModelSize.LARGE, ModelSize.MEDIUM]:
                # Anthropic API call
                response = await self._call_anthropic_api(model_size.value, prompt)
                return response.get("content", [{}])[0].get("text", "")
            else:
                # Local model API call
                response = await self._call_local_model_api(config["api_base"], prompt)
                return response.get("choices", [{}])[0].get("message", {}).get("content", "")
                
        except Exception as e:
            logger.error(f"Summary generation failed for {model_size.value}", error=str(e))
            return "Summary generation failed"

    async def _call_anthropic_api(self, model: str, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API for large/medium models"""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150
            }
            
            async with self.session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                return await response.json()
                
        except Exception as e:
            logger.error("Anthropic API call failed", error=str(e))
            return {"content": [{"text": "API call failed"}]}

    async def _call_local_model_api(self, api_base: str, prompt: str) -> Dict[str, Any]:
        """Call local model API for small models"""
        try:
            payload = {
                "model": "local",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.1
            }
            
            async with self.session.post(api_base, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"choices": [{"message": {"content": "Local API unavailable"}}]}
                    
        except Exception as e:
            logger.warning("Local model API call failed", api_base=api_base, error=str(e))
            return {"choices": [{"message": {"content": "Local model unavailable"}}]}

    def _evaluate_summary_accuracy(self, article: NewsArticle, summary: str) -> float:
        """
        COT: Evaluate factual accuracy of generated summary
        Simple keyword overlap and length appropriateness
        """
        if not summary or summary == "Summary generation failed":
            return 0.0
        
        # Simple accuracy metrics
        word_count = len(summary.split())
        appropriate_length = 0.8 if 30 <= word_count <= 120 else 0.4
        
        # Keyword overlap with original content
        article_keywords = set(article.content.lower().split())
        summary_keywords = set(summary.lower().split())
        overlap_ratio = len(article_keywords & summary_keywords) / max(len(summary_keywords), 1)
        
        # Combined accuracy score
        return min(1.0, appropriate_length + overlap_ratio * 0.5)

    def _evaluate_summary_quality(self, summary: str) -> float:
        """
        COT: Evaluate overall quality of summary
        Considers readability, coherence, completeness
        """
        if not summary or len(summary) < 20:
            return 0.0
        
        # Quality indicators
        sentence_count = len([s for s in summary.split('.') if s.strip()])
        appropriate_sentences = 0.9 if 2 <= sentence_count <= 4 else 0.5
        
        # Check for common quality markers
        quality_markers = [
            "according to", "reported", "announced", "stated",
            "officials", "sources", "data", "study"
        ]
        
        marker_score = sum(1 for marker in quality_markers if marker in summary.lower()) / len(quality_markers)
        
        return min(1.0, appropriate_sentences + marker_score * 0.3)

    def _estimate_request_cost(self, config: Dict[str, Any], summary: str) -> float:
        """Estimate cost per request based on token usage"""
        token_count = len(summary.split()) * 1.3  # Rough token estimation
        return token_count * config["cost_per_token"]

    def _calculate_factual_consistency(self, model_size: ModelSize) -> float:
        """
        COT: Calculate consistency with reference model
        In production, would compare outputs with reference
        """
        # Simplified consistency based on model expectations
        expected_quality = self.model_configs[model_size]["expected_quality"]
        return expected_quality

    def _calculate_efficiency_ratios(
        self, 
        performance_results: Dict[str, ModelPerformanceMetrics]
    ) -> Dict[str, ModelPerformanceMetrics]:
        """
        COT: Calculate efficiency ratios (quality/cost)
        Higher ratio = better efficiency
        """
        for model_name, metrics in performance_results.items():
            if metrics.cost_per_request > 0:
                metrics.efficiency_ratio = metrics.quality_score / metrics.cost_per_request
            else:
                metrics.efficiency_ratio = metrics.quality_score  # Free model

        return performance_results

    def _select_optimal_model(
        self,
        efficiency_results: Dict[str, ModelPerformanceMetrics],
        quality_priority: bool
    ) -> str:
        """
        COT: Select optimal model based on efficiency and constraints
        Balance quality, speed, and cost requirements
        """
        # Filter models that pass benchmarks
        valid_models = {
            name: metrics for name, metrics in efficiency_results.items()
            if metrics.benchmark_passed and metrics.accuracy_score >= self.accuracy_threshold
        }
        
        if not valid_models:
            logger.warning("No models passed benchmarks, falling back to reference")
            return ModelSize.LARGE.value
        
        if quality_priority:
            # Prioritize quality over cost
            optimal = max(valid_models.items(), key=lambda x: x[1].quality_score)
        else:
            # Prioritize efficiency (quality/cost ratio)
            optimal = max(valid_models.items(), key=lambda x: x[1].efficiency_ratio)
        
        return optimal[0]

    def _generate_optimization_result(
        self,
        optimal_model: str,
        efficiency_results: Dict[str, ModelPerformanceMetrics]
    ) -> ELearnFitResult:
        """
        COT: Generate comprehensive optimization result
        Include recommendations and fallback strategies
        """
        optimal_metrics = efficiency_results[optimal_model]
        reference_metrics = efficiency_results.get(ModelSize.LARGE.value)
        
        # Calculate cost savings
        cost_savings = 0.0
        if reference_metrics and reference_metrics.cost_per_request > 0:
            cost_savings = (1 - optimal_metrics.cost_per_request / reference_metrics.cost_per_request) * 100
        
        # Quality maintained check
        quality_maintained = optimal_metrics.quality_score >= self.accuracy_threshold
        
        # Generate reasoning
        reasoning = self._generate_optimization_reasoning(optimal_model, optimal_metrics)
        
        # Fallback strategy
        fallback_strategy = self._determine_fallback_strategy(efficiency_results)

        return ELearnFitResult(
            recommended_model=optimal_model,
            performance_comparison=efficiency_results,
            cost_savings_percent=cost_savings,
            quality_maintained=quality_maintained,
            fallback_strategy=fallback_strategy,
            optimization_reasoning=reasoning
        )

    def _generate_optimization_reasoning(
        self, 
        model: str, 
        metrics: ModelPerformanceMetrics
    ) -> str:
        """Generate human-readable optimization reasoning"""
        reasons = []
        
        if metrics.efficiency_ratio > 1000:  # High efficiency
            reasons.append(f"Excellent efficiency ratio ({metrics.efficiency_ratio:.0f})")
        
        if metrics.speed_ms < 200:
            reasons.append(f"Fast response time ({metrics.speed_ms:.0f}ms)")
        
        if metrics.accuracy_score > 0.9:
            reasons.append(f"High accuracy ({metrics.accuracy_score:.1%})")
        
        if metrics.cost_per_request < 0.001:
            reasons.append("Very low cost per request")
        
        return " • ".join(reasons) if reasons else "Meets minimum requirements"

    def _determine_fallback_strategy(
        self, 
        efficiency_results: Dict[str, ModelPerformanceMetrics]
    ) -> str:
        """Determine fallback strategy if optimal model fails"""
        # Find second-best model
        sorted_models = sorted(
            efficiency_results.items(),
            key=lambda x: x[1].efficiency_ratio,
            reverse=True
        )
        
        if len(sorted_models) >= 2:
            fallback_model = sorted_models[1][0]
            return f"Fallback to {fallback_model} if primary model unavailable"
        else:
            return f"Fallback to {ModelSize.LARGE.value} (reference model)"

    def _create_benchmark_dataset(self) -> List[NewsArticle]:
        """Create standardized benchmark dataset for testing"""
        # Create sample articles for benchmarking
        return [
            NewsArticle(
                id="bench_1",
                title="Technology Company Announces Quarterly Results",
                content="A major technology company reported strong quarterly earnings today, exceeding analyst expectations by 15%. The company's revenue grew by 12% year-over-year, driven by increased demand for cloud services and artificial intelligence products. CEO stated that the results reflect successful strategic investments in emerging technologies.",
                source="TechNews",
                url="https://example.com/bench1",
                published_at=datetime.now(),
                credibility_score=0.9
            ),
            NewsArticle(
                id="bench_2", 
                title="Climate Summit Reaches Historic Agreement",
                content="World leaders at the international climate summit reached a historic agreement on carbon emissions reduction. The agreement includes commitments from 195 countries to reduce greenhouse gas emissions by 50% by 2030. Environmental groups praised the agreement while noting implementation challenges remain.",
                source="GlobalNews",
                url="https://example.com/bench2",
                published_at=datetime.now(),
                credibility_score=0.95
            ),
            NewsArticle(
                id="bench_3",
                title="Medical Research Breakthrough Shows Promise",
                content="Researchers at a leading medical institution announced a breakthrough in treatment for a rare genetic disorder. The experimental therapy showed 85% success rate in clinical trials involving 200 patients. The treatment could potentially help thousands of patients worldwide who currently have limited options.",
                source="MedicalJournal",
                url="https://example.com/bench3", 
                published_at=datetime.now(),
                credibility_score=0.93
            )
        ]


# E-LearnFit Integration with News Pipeline
class AdaptiveModelManager:
    """
    COT: Dynamically manage model selection based on workload
    Switch between models based on real-time performance metrics
    """
    
    def __init__(self, elearnfit_optimizer: ELearnFitOptimizer):
        self.optimizer = elearnfit_optimizer
        self.current_model = ModelSize.LARGE.value  # Default
        self.performance_history = []
        self.optimization_interval = 3600  # Re-optimize every hour
        self.last_optimization = datetime.now()

    async def get_optimal_model_for_task(self, task_priority: str = "balanced") -> str:
        """
        COT: Get optimal model for current task
        Consider recent performance and current workload
        """
        # Check if re-optimization is needed
        if self._should_reoptimize():
            await self._trigger_reoptimization(task_priority)
        
        return self.current_model

    def _should_reoptimize(self) -> bool:
        """Check if model reoptimization is needed"""
        time_since_optimization = (datetime.now() - self.last_optimization).seconds
        return time_since_optimization >= self.optimization_interval

    async def _trigger_reoptimization(self, priority: str):
        """Trigger E-LearnFit reoptimization"""
        try:
            quality_priority = priority == "quality"
            async with self.optimizer as opt:
                result = await opt.optimize_model_selection(quality_priority=quality_priority)
                self.current_model = result.recommended_model
                self.last_optimization = datetime.now()
                
                logger.info(
                    "Model reoptimized",
                    new_model=self.current_model,
                    cost_savings=result.cost_savings_percent
                )
        except Exception as e:
            logger.error("Model reoptimization failed", error=str(e))
            # Keep current model on failure
