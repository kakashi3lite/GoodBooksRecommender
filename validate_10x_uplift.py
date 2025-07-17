#!/usr/bin/env python3
"""
10× Uplift Validation Runner
===========================

Executive validation script for measuring and validating 10× uplift in newsletter transformation.
Implements comprehensive testing, reporting, and evidence generation.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import our validation framework
sys.path.append(str(Path(__file__).parent))
from src.newsletter.validation.kpi_validator import create_kpi_validator, ValidationResult

class UpliftValidationRunner:
    """Production-grade validation runner for 10× uplift measurement"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url
        self.validator = None
        self.results_dir = Path("reports/validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize validation components"""
        try:
            logger.info("Initializing 10× Uplift Validation Runner...")
            self.validator = await create_kpi_validator(self.database_url)
            logger.info("✅ Validation runner initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize validation runner: {e}")
            raise

    async def run_full_validation(self) -> ValidationResult:
        """Run comprehensive 10× uplift validation"""
        try:
            logger.info("🚀 Starting comprehensive 10× uplift validation...")
            
            start_time = time.time()
            
            # Run the validation
            result = await self.validator.run_comprehensive_validation()
            
            duration = time.time() - start_time
            logger.info(f"⏱️ Validation completed in {duration:.2f} seconds")
            
            # Generate comprehensive report
            report = await self.validator.generate_validation_report()
            
            # Save results
            await self._save_validation_results(result, report, duration)
            
            # Print summary
            self._print_validation_summary(result, report)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            raise

    async def _save_validation_results(self, result: ValidationResult, report: Dict[str, Any], duration: float):
        """Save validation results to files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save detailed JSON report
            report_file = self.results_dir / f"validation_report_{timestamp}.json"
            enhanced_report = {
                "validation_metadata": {
                    "timestamp": result.validation_timestamp.isoformat(),
                    "duration_seconds": duration,
                    "runner_version": "1.0.0",
                    "validation_type": "10x_uplift_comprehensive"
                },
                "executive_summary": report["summary"],
                "detailed_metrics": report["detailed_metrics"],
                "trend_analysis": report.get("trend_analysis", {}),
                "recommendations": report["recommendations"],
                "raw_metrics": [
                    {
                        "name": m.name,
                        "current_value": m.current_value,
                        "baseline_value": m.baseline_value,
                        "target_value": m.target_value,
                        "improvement_factor": m.improvement_factor,
                        "target_achieved": m.target_achieved,
                        "confidence_level": m.confidence_level,
                        "sample_size": m.sample_size,
                        "unit": m.unit
                    }
                    for m in result.metrics
                ]
            }
            
            with open(report_file, 'w') as f:
                json.dump(enhanced_report, f, indent=2, default=str)
            
            # Export full validation data
            data_file = self.results_dir / f"validation_data_{timestamp}.json"
            await self.validator.export_validation_data(str(data_file))
            
            # Generate markdown report
            await self._generate_markdown_report(enhanced_report, timestamp)
            
            logger.info(f"✅ Results saved to {report_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save validation results: {e}")
            raise

    async def _generate_markdown_report(self, report: Dict[str, Any], timestamp: str):
        """Generate markdown validation report"""
        try:
            markdown_file = self.results_dir / f"validation_report_{timestamp}.md"
            
            md_content = f"""# 🎯 10× Uplift Validation Report

**Validation Date:** {report['validation_metadata']['timestamp']}  
**Duration:** {report['validation_metadata']['duration_seconds']:.2f} seconds  
**Validation Type:** {report['validation_metadata']['validation_type']}

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Uplift Achieved** | {'✅ YES' if report['executive_summary']['overall_uplift_achieved'] else '❌ NO'} |
| **Average Improvement Factor** | {report['executive_summary']['average_improvement_factor']} |
| **Metrics Passing** | {report['executive_summary']['metrics_passing']} |
| **Success Rate** | {report['executive_summary']['success_rate']} |
| **Confidence Score** | {report['executive_summary']['confidence_score']} |

---

## 📈 Detailed Metrics Results

| Metric | Current | Baseline | Target | Improvement | Status | Confidence |
|--------|---------|----------|---------|-------------|--------|------------|
"""
            
            for metric_name, data in report['detailed_metrics'].items():
                status = "✅ PASS" if data['target_achieved'] else "❌ FAIL"
                md_content += f"| {metric_name.replace('_', ' ').title()} | {data['current_value']:.3f} {data['unit']} | {data['baseline_value']:.3f} {data['unit']} | {data['target_value']:.3f} {data['unit']} | {data['improvement_factor']} | {status} | {data['confidence_level']} |\n"
            
            md_content += f"""
---

## 🎯 Key Achievements

"""
            
            # Add achievements for metrics that achieved significant uplift
            high_performers = [
                (name, data) for name, data in report['detailed_metrics'].items()
                if data['target_achieved'] and float(data['improvement_factor'].rstrip('×')) >= 10.0
            ]
            
            if high_performers:
                md_content += "### 🏆 Metrics Achieving 10× Uplift:\n\n"
                for name, data in high_performers:
                    md_content += f"- **{name.replace('_', ' ').title()}**: {data['improvement_factor']} improvement\n"
            
            good_performers = [
                (name, data) for name, data in report['detailed_metrics'].items()
                if data['target_achieved'] and 5.0 <= float(data['improvement_factor'].rstrip('×')) < 10.0
            ]
            
            if good_performers:
                md_content += "\n### 📈 Metrics with Strong Performance (5× - 10×):\n\n"
                for name, data in good_performers:
                    md_content += f"- **{name.replace('_', ' ').title()}**: {data['improvement_factor']} improvement\n"
            
            md_content += f"""
---

## 💡 Recommendations

"""
            for i, rec in enumerate(report['recommendations'], 1):
                md_content += f"{i}. {rec}\n"
            
            if report.get('trend_analysis'):
                md_content += f"""
---

## 📊 Trend Analysis

| Metric | Change |
|--------|--------|
| Improvement Trend | {report['trend_analysis']['improvement_trend']:+.2f}× |
| Metrics Passing Trend | {report['trend_analysis']['metrics_trend']:+d} metrics |
| Confidence Trend | {report['trend_analysis']['confidence_trend']:+.3f} |
"""
            
            md_content += f"""
---

## 🔗 Related Files

- **Detailed JSON Report**: `validation_report_{timestamp}.json`
- **Raw Validation Data**: `validation_data_{timestamp}.json`
- **Validation Logs**: `logs/validation.log`

---

*Generated by 10× Uplift Validation Runner v{report['validation_metadata']['runner_version']}*
"""
            
            with open(markdown_file, 'w') as f:
                f.write(md_content)
            
            logger.info(f"✅ Markdown report generated: {markdown_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate markdown report: {e}")

    def _print_validation_summary(self, result: ValidationResult, report: Dict[str, Any]):
        """Print validation summary to console"""
        print("\n" + "="*80)
        print("🎯 10× UPLIFT VALIDATION SUMMARY")
        print("="*80)
        
        print(f"\n📊 OVERALL RESULT: {'✅ SUCCESS' if result.overall_uplift_achieved else '❌ NEEDS IMPROVEMENT'}")
        print(f"📈 Average Improvement: {result.average_improvement_factor:.2f}×")
        print(f"📋 Metrics Passing: {result.metrics_passing}/{result.total_metrics}")
        print(f"🎯 Success Rate: {(result.metrics_passing/result.total_metrics)*100:.1f}%")
        print(f"🔍 Confidence Score: {result.confidence_score*100:.1f}%")
        
        print("\n📈 METRIC BREAKDOWN:")
        print("-" * 80)
        print(f"{'Metric':<25} {'Current':<12} {'Target':<12} {'Improvement':<12} {'Status'}")
        print("-" * 80)
        
        for metric in result.metrics:
            status = "✅ PASS" if metric.target_achieved else "❌ FAIL"
            print(f"{metric.name:<25} {metric.current_value:<12.3f} {metric.target_value:<12.3f} {metric.improvement_factor:<12.2f}× {status}")
        
        print("\n💡 TOP RECOMMENDATIONS:")
        print("-" * 80)
        for i, rec in enumerate(result.recommendations[:5], 1):
            print(f"{i}. {rec}")
        
        print("\n" + "="*80)

    async def run_quick_validation(self) -> Dict[str, Any]:
        """Run quick validation for development/testing"""
        try:
            logger.info("🏃‍♂️ Running quick validation...")
            
            # Run subset of critical metrics
            engagement_metric = await self.validator.measure_user_engagement()
            ctr_metric = await self.validator.measure_click_through_rate()
            response_time_metric = await self.validator.measure_response_time()
            
            quick_metrics = [engagement_metric, ctr_metric, response_time_metric]
            
            metrics_passing = sum(1 for m in quick_metrics if m.target_achieved)
            avg_improvement = sum(m.improvement_factor for m in quick_metrics) / len(quick_metrics)
            
            result = {
                "quick_validation": True,
                "metrics_tested": len(quick_metrics),
                "metrics_passing": metrics_passing,
                "average_improvement": f"{avg_improvement:.2f}×",
                "overall_status": "PASS" if metrics_passing >= 2 else "NEEDS_WORK",
                "metrics": [
                    {
                        "name": m.name,
                        "improvement": f"{m.improvement_factor:.2f}×",
                        "status": "PASS" if m.target_achieved else "FAIL"
                    }
                    for m in quick_metrics
                ]
            }
            
            print("\n🏃‍♂️ QUICK VALIDATION SUMMARY:")
            print(f"Status: {result['overall_status']}")
            print(f"Metrics Passing: {metrics_passing}/{len(quick_metrics)}")
            print(f"Average Improvement: {result['average_improvement']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Quick validation failed: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.validator:
                await self.validator.cleanup()
            logger.info("✅ Validation runner cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

async def main():
    """Main validation runner function"""
    parser = argparse.ArgumentParser(description="10× Uplift Validation Runner")
    parser.add_argument("--quick", action="store_true", help="Run quick validation")
    parser.add_argument("--database-url", help="Database URL for storage")
    parser.add_argument("--output-dir", default="reports/validation", help="Output directory for reports")
    
    args = parser.parse_args()
    
    runner = None
    try:
        # Initialize runner
        runner = UpliftValidationRunner(database_url=args.database_url)
        if args.output_dir:
            runner.results_dir = Path(args.output_dir)
            runner.results_dir.mkdir(parents=True, exist_ok=True)
            
        await runner.initialize()
        
        # Run validation
        if args.quick:
            result = await runner.run_quick_validation()
            print(f"\n✅ Quick validation completed: {result['overall_status']}")
        else:
            result = await runner.run_full_validation()
            if result.overall_uplift_achieved:
                print("\n🎉 10× UPLIFT SUCCESSFULLY ACHIEVED! 🎉")
            else:
                print(f"\n📈 Progress made: {result.average_improvement_factor:.2f}× average improvement")
                print("Continue iterating to achieve full 10× uplift target")
        
        return 0 if (result.overall_uplift_achieved if hasattr(result, 'overall_uplift_achieved') else result['overall_status'] == 'PASS') else 1
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return 1
    finally:
        if runner:
            await runner.cleanup()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
