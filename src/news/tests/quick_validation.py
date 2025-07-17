"""
Superhuman AI News Engine - Quick Integration Validation
Validates all components are working and accessible
COT: Start with basic validation, then expand to full testing
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle

logger = StructuredLogger(__name__)


async def quick_validation_test():
    """
    COT: Quick validation that all components can be imported and instantiated
    Validates basic functionality without complex scenarios
    """
    logger.info("🚀 Starting Quick Superhuman AI News Engine Validation")
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "component_imports": {},
        "basic_functionality": {},
        "overall_status": "unknown"
    }
    
    # Test 1: Component Import Validation
    logger.info("Testing component imports...")
    
    try:
        # Test ScoreRAG import
        from src.news.ai.scorerag_summarization import ScoreRAGProcessor
        validation_results["component_imports"]["scorerag"] = {"status": "success", "class": "ScoreRAGProcessor"}
    except Exception as e:
        validation_results["component_imports"]["scorerag"] = {"status": "failed", "error": str(e)}
    
    try:
        # Test E-LearnFit import
        from src.news.ai.elearnfit_optimizer import ELearnFitOptimizer
        validation_results["component_imports"]["elearnfit"] = {"status": "success", "class": "ELearnFitOptimizer"}
    except Exception as e:
        validation_results["component_imports"]["elearnfit"] = {"status": "failed", "error": str(e)}
    
    try:
        # Test GNR import
        from src.news.personalization.generative_recommender import GenerativeNewsRecommender
        validation_results["component_imports"]["gnr"] = {"status": "success", "class": "GenerativeNewsRecommender"}
    except Exception as e:
        validation_results["component_imports"]["gnr"] = {"status": "failed", "error": str(e)}
    
    try:
        # Test Particle Feed import
        from src.news.ui.particle_feed import ParticleStyleFeedManager
        validation_results["component_imports"]["particle_feed"] = {"status": "success", "class": "ParticleStyleFeedManager"}
    except Exception as e:
        validation_results["component_imports"]["particle_feed"] = {"status": "failed", "error": str(e)}
    
    try:
        # Test Optimized Personalization import
        from src.news.personalization.optimized_engine import OptimizedPersonalizationEngine
        validation_results["component_imports"]["personalization"] = {"status": "success", "class": "OptimizedPersonalizationEngine"}
    except Exception as e:
        validation_results["component_imports"]["personalization"] = {"status": "failed", "error": str(e)}
    
    try:
        # Test Master Engine import
        from src.news.master.superhuman_engine import SuperhumanNewsEngine
        validation_results["component_imports"]["master_engine"] = {"status": "success", "class": "SuperhumanNewsEngine"}
    except Exception as e:
        validation_results["component_imports"]["master_engine"] = {"status": "failed", "error": str(e)}
    
    # Test 2: Basic Instantiation
    logger.info("Testing basic instantiation...")
    
    try:
        # Create sample article for testing
        test_article = NewsArticle(
            id="test_001",
            title="Sample News Article for Testing",
            content="This is a sample news article used for testing the superhuman AI news engine. It contains enough content to test basic processing capabilities and component integration. The article discusses technology, innovation, and future trends in artificial intelligence.",
            source="Test News Source",
            url="https://test.example.com/article/001",
            published_at=datetime.now() - timedelta(hours=1),
            topics=["technology", "ai", "innovation"],
            credibility_score=0.9,
            reading_time_minutes=3
        )
        
        validation_results["basic_functionality"]["test_article_creation"] = {
            "status": "success",
            "article_id": test_article.id
        }
        
    except Exception as e:
        validation_results["basic_functionality"]["test_article_creation"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Test 3: Component Instantiation
    if validation_results["component_imports"]["master_engine"]["status"] == "success":
        try:
            # Test master engine instantiation
            from src.news.master.superhuman_engine import SuperhumanNewsEngine
            
            # Quick instantiation test (without async context)
            engine = SuperhumanNewsEngine()
            
            validation_results["basic_functionality"]["master_engine_instantiation"] = {
                "status": "success",
                "components_initialized": True
            }
            
        except Exception as e:
            validation_results["basic_functionality"]["master_engine_instantiation"] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Test 4: Performance Baseline
    logger.info("Testing performance baseline...")
    
    try:
        start_time = time.time()
        
        # Simple performance test - create multiple articles
        test_articles = []
        for i in range(5):
            article = NewsArticle(
                id=f"perf_test_{i:03d}",
                title=f"Performance Test Article {i+1}",
                content=f"This is performance test article number {i+1}. " * 20,  # 20x repetition
                source="Performance Test Source",
                url=f"https://test.example.com/perf/{i}",
                published_at=datetime.now() - timedelta(hours=i),
                topics=["testing", "performance"],
                credibility_score=0.8 + (i * 0.02),
                reading_time_minutes=2 + i
            )
            test_articles.append(article)
        
        creation_time = (time.time() - start_time) * 1000
        
        validation_results["basic_functionality"]["performance_baseline"] = {
            "status": "success",
            "articles_created": len(test_articles),
            "creation_time_ms": creation_time,
            "avg_time_per_article_ms": creation_time / len(test_articles)
        }
        
    except Exception as e:
        validation_results["basic_functionality"]["performance_baseline"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Assessment
    import_successes = sum(1 for result in validation_results["component_imports"].values() if result["status"] == "success")
    total_imports = len(validation_results["component_imports"])
    
    functionality_successes = sum(1 for result in validation_results["basic_functionality"].values() if result["status"] == "success")
    total_functionality = len(validation_results["basic_functionality"])
    
    overall_success_rate = (import_successes + functionality_successes) / (total_imports + total_functionality)
    
    if overall_success_rate >= 0.9:
        validation_results["overall_status"] = "excellent"
    elif overall_success_rate >= 0.8:
        validation_results["overall_status"] = "good"
    elif overall_success_rate >= 0.7:
        validation_results["overall_status"] = "fair"
    else:
        validation_results["overall_status"] = "needs_attention"
    
    validation_results["summary"] = {
        "import_success_rate": import_successes / total_imports,
        "functionality_success_rate": functionality_successes / total_functionality,
        "overall_success_rate": overall_success_rate,
        "total_tests": total_imports + total_functionality,
        "passed_tests": import_successes + functionality_successes
    }
    
    # Save results
    with open("quick_validation_results.json", "w") as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(
        "🎯 Quick validation completed",
        overall_status=validation_results["overall_status"],
        success_rate=f"{overall_success_rate:.1%}",
        results_file="quick_validation_results.json"
    )
    
    return validation_results


async def test_individual_components():
    """
    COT: Test each component individually to identify specific issues
    """
    logger.info("🔧 Testing Individual Components")
    
    component_results = {}
    
    # Test ScoreRAG Component
    try:
        from src.news.ai.scorerag_summarization import ScoreRAGProcessor
        
        async with ScoreRAGProcessor() as processor:
            # Basic functionality test
            test_articles = [
                NewsArticle(
                    id="scorerag_test_1",
                    title="Test Article 1",
                    content="This is test content for ScoreRAG processing. It contains factual information about technology trends.",
                    source="Test Source",
                    url="https://test.example.com/scorerag/1",
                    published_at=datetime.now(),
                    topics=["technology"],
                    credibility_score=0.9,
                    reading_time_minutes=2
                )
            ]
            
            summary = await processor.generate_scorerag_summary(
                query="Technology trends",
                articles=test_articles,
                max_summary_length=100
            )
            
            component_results["scorerag"] = {
                "status": "success",
                "summary_generated": summary is not None,
                "summary_length": len(summary.summary_text) if summary else 0
            }
            
    except Exception as e:
        component_results["scorerag"] = {"status": "failed", "error": str(e)}
    
    # Test E-LearnFit Component  
    try:
        from src.news.ai.elearnfit_optimizer import ELearnFitOptimizer
        
        optimizer = ELearnFitOptimizer()
        
        # Basic functionality test
        result = await optimizer.optimize_model_selection()
        
        component_results["elearnfit"] = {
            "status": "success",
            "optimization_completed": result is not None,
            "result_type": type(result).__name__ if result else "None"
        }
        
    except Exception as e:
        component_results["elearnfit"] = {"status": "failed", "error": str(e)}
    
    # Test GNR Component
    try:
        from src.news.personalization.generative_recommender import GenerativeNewsRecommender
        from src.news.ai.scorerag_summarization import ScoreRAGProcessor
        
        scorerag = ScoreRAGProcessor()
        
        async with GenerativeNewsRecommender(scorerag) as gnr:
            # Basic functionality test
            test_articles = [
                NewsArticle(
                    id="gnr_test_1",
                    title="Related Story 1",
                    content="This is a related story for narrative generation testing.",
                    source="Test Source",
                    url="https://test.example.com/gnr/1",
                    published_at=datetime.now(),
                    topics=["technology"],
                    credibility_score=0.9,
                    reading_time_minutes=2
                )
            ]
            
            narratives = await gnr.generate_narrative_recommendations(
                user_id="test_user",
                candidate_articles=test_articles,
                user_interests={"technology": 0.8},
                max_stories=1
            )
            
            component_results["gnr"] = {
                "status": "success",
                "narratives_generated": len(narratives),
                "narrative_quality": "basic" if narratives else "none"
            }
            
    except Exception as e:
        component_results["gnr"] = {"status": "failed", "error": str(e)}
    
    logger.info("Individual component testing completed", results=component_results)
    return component_results


if __name__ == "__main__":
    # Run quick validation
    results = asyncio.run(quick_validation_test())
    
    # Run individual component tests
    component_results = asyncio.run(test_individual_components())
    
    print("\n" + "="*60)
    print("🚀 SUPERHUMAN AI NEWS ENGINE - QUICK VALIDATION RESULTS")
    print("="*60)
    
    print(f"\n📊 Overall Status: {results['overall_status'].upper()}")
    print(f"📈 Success Rate: {results['summary']['overall_success_rate']:.1%}")
    print(f"✅ Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    
    print("\n🔧 Component Import Status:")
    for component, result in results["component_imports"].items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {component}: {result['status']}")
    
    print("\n⚙️ Basic Functionality Status:")
    for func, result in results["basic_functionality"].items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {func}: {result['status']}")
    
    print("\n🧪 Individual Component Test Results:")
    for component, result in component_results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {component}: {result['status']}")
    
    if results["overall_status"] in ["excellent", "good"]:
        print("\n🎉 VALIDATION SUCCESSFUL - System ready for full integration testing!")
    else:
        print("\n⚠️  VALIDATION ISSUES DETECTED - Review component errors before proceeding")
    
    print("\n📁 Detailed results saved to: quick_validation_results.json")
    print("="*60)
