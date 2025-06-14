import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from src.config import Config
from src.analytics.user_analytics import UserAnalytics
from src.analytics.cohort_analysis import CohortAnalysis
from src.analytics.recommendation_metrics import RecommendationMetrics

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self,
                 config: Config,
                 user_analytics: UserAnalytics,
                 cohort_analysis: CohortAnalysis,
                 recommendation_metrics: RecommendationMetrics):
        self.config = config
        self.user_analytics = user_analytics
        self.cohort_analysis = cohort_analysis
        self.recommendation_metrics = recommendation_metrics
        self.report_data: Dict[str, Any] = {}
        
        # Set up plotting style
        plt.style.use('seaborn')
        sns.set_palette('husl')
    
    def generate_report(self,
                       report_type: str = 'full',
                       time_window: Optional[timedelta] = None,
                       output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        try:
            # Set default output directory
            output_dir = output_dir or self.config.get_reports_dir()
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate report sections based on type
            if report_type == 'full' or report_type == 'user':
                self.report_data['user_analytics'] = self._generate_user_analytics_report(time_window)
            
            if report_type == 'full' or report_type == 'cohort':
                self.report_data['cohort_analysis'] = self._generate_cohort_analysis_report(time_window)
            
            if report_type == 'full' or report_type == 'recommendation':
                self.report_data['recommendation_metrics'] = self._generate_recommendation_metrics_report(time_window)
            
            # Generate visualizations
            self._generate_visualizations(output_dir)
            
            # Save report data
            self._save_report_data(output_dir)
            
            return self.report_data
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _generate_user_analytics_report(self,
                                       time_window: Optional[timedelta]) -> Dict[str, Any]:
        """Generate user analytics section of the report."""
        try:
            # Get user segments
            user_segments = self.user_analytics.user_segments
            
            # Calculate segment metrics
            segment_metrics = {}
            for segment, users in user_segments.items():
                segment_data = []
                for user_id in users:
                    analysis = self.user_analytics.analyze_user_behavior(user_id, time_window)
                    segment_data.append(analysis)
                
                segment_metrics[segment] = self._aggregate_segment_metrics(segment_data)
            
            report = {
                'segment_analysis': segment_metrics,
                'engagement_trends': self._analyze_engagement_trends(segment_metrics),
                'user_behavior_patterns': self._analyze_behavior_patterns(segment_metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating user analytics report: {str(e)}")
            raise
    
    def _aggregate_segment_metrics(self, segment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate metrics for a user segment."""
        try:
            if not segment_data:
                return {}
            
            aggregated = {
                'size': len(segment_data),
                'engagement': {
                    'average_score': np.mean([d['engagement_metrics']['engagement_score'] for d in segment_data]),
                    'activity_frequency': np.mean([d['engagement_metrics']['activity_frequency'] for d in segment_data]),
                    'retention_rate': np.mean([d['engagement_metrics']['retention_score'] for d in segment_data])
                },
                'preferences': {
                    'diversity': np.mean([d['preference_analysis']['diversity_index'] for d in segment_data]),
                    'stability': np.mean([d['preference_analysis']['preference_stability'] for d in segment_data])
                }
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating segment metrics: {str(e)}")
            raise
    
    def _analyze_engagement_trends(self, segment_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement trends across segments."""
        try:
            trends = {
                'segment_comparison': {
                    segment: metrics['engagement']
                    for segment, metrics in segment_metrics.items()
                },
                'overall_engagement': np.mean([
                    metrics['engagement']['average_score']
                    for metrics in segment_metrics.values()
                ])
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {str(e)}")
            raise
    
    def _analyze_behavior_patterns(self, segment_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavior patterns across segments."""
        try:
            patterns = {
                'preference_stability': {
                    segment: metrics['preferences']['stability']
                    for segment, metrics in segment_metrics.items()
                },
                'preference_diversity': {
                    segment: metrics['preferences']['diversity']
                    for segment, metrics in segment_metrics.items()
                }
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing behavior patterns: {str(e)}")
            raise
    
    def _generate_cohort_analysis_report(self,
                                        time_window: Optional[timedelta]) -> Dict[str, Any]:
        """Generate cohort analysis section of the report."""
        try:
            # Get cohort analysis
            cohort_analysis = self.cohort_analysis.analyze_cohorts(time_window)
            
            report = {
                'retention_analysis': self._analyze_retention_metrics(cohort_analysis),
                'engagement_analysis': self._analyze_cohort_engagement(cohort_analysis),
                'value_analysis': self._analyze_cohort_value(cohort_analysis)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating cohort analysis report: {str(e)}")
            raise
    
    def _analyze_retention_metrics(self, cohort_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze retention metrics from cohort analysis."""
        try:
            retention_data = cohort_analysis.get('retention', {})
            
            analysis = {
                'overall_retention': np.mean([
                    rate for rates in retention_data.get('retention_matrix', {}).values()
                    for rate in rates.values()
                ]),
                'retention_by_cohort': retention_data.get('retention_matrix', {}),
                'trends': retention_data.get('retention_trends', {})
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing retention metrics: {str(e)}")
            raise
    
    def _analyze_cohort_engagement(self, cohort_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement metrics from cohort analysis."""
        try:
            engagement_data = cohort_analysis.get('engagement', {})
            
            analysis = {
                'average_engagement': engagement_data.get('average_engagement', {}),
                'engagement_trends': engagement_data.get('engagement_trends', {}),
                'patterns': engagement_data.get('activity_patterns', {})
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing cohort engagement: {str(e)}")
            raise
    
    def _analyze_cohort_value(self, cohort_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze value metrics from cohort analysis."""
        try:
            value_data = cohort_analysis.get('lifetime_value', {})
            
            analysis = {
                'average_ltv': value_data.get('average_ltv', 0),
                'ltv_distribution': value_data.get('ltv_distribution', {}),
                'value_progression': value_data.get('value_progression', {})
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing cohort value: {str(e)}")
            raise
    
    def _generate_recommendation_metrics_report(self,
                                               time_window: Optional[timedelta]) -> Dict[str, Any]:
        """Generate recommendation metrics section of the report."""
        try:
            # Get recommendation metrics
            metrics = self.recommendation_metrics.calculate_metrics(time_window)
            
            report = {
                'accuracy_metrics': self._analyze_accuracy_metrics(metrics),
                'diversity_metrics': self._analyze_diversity_metrics(metrics),
                'business_impact': self._analyze_business_impact(metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating recommendation metrics report: {str(e)}")
            raise
    
    def _analyze_accuracy_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze accuracy metrics from recommendation analysis."""
        try:
            accuracy_data = metrics.get('accuracy', {})
            
            analysis = {
                'precision': accuracy_data.get('precision', {}),
                'recall': accuracy_data.get('recall', {}),
                'ndcg': accuracy_data.get('ndcg', {}),
                'ranking_quality': metrics.get('ranking', {})
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing accuracy metrics: {str(e)}")
            raise
    
    def _analyze_diversity_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze diversity metrics from recommendation analysis."""
        try:
            diversity_data = metrics.get('diversity', {})
            
            analysis = {
                'item_coverage': diversity_data.get('item_coverage', 0),
                'category_coverage': diversity_data.get('category_coverage', 0),
                'serendipity': diversity_data.get('serendipity', 0)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing diversity metrics: {str(e)}")
            raise
    
    def _analyze_business_impact(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business impact metrics from recommendation analysis."""
        try:
            business_data = metrics.get('business', {})
            
            analysis = {
                'conversion_rate': business_data.get('conversion_rate', 0),
                'revenue_impact': business_data.get('revenue_impact', 0),
                'user_satisfaction': business_data.get('user_satisfaction', 0)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing business impact: {str(e)}")
            raise
    
    def _generate_visualizations(self, output_dir: str) -> None:
        """Generate visualizations for the report."""
        try:
            # User segment visualization
            self._plot_user_segments(output_dir)
            
            # Retention visualization
            self._plot_retention_heatmap(output_dir)
            
            # Engagement trends visualization
            self._plot_engagement_trends(output_dir)
            
            # Recommendation performance visualization
            self._plot_recommendation_performance(output_dir)
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
    
    def _plot_user_segments(self, output_dir: str) -> None:
        """Create visualization for user segments."""
        try:
            if 'user_analytics' not in self.report_data:
                return
            
            segment_data = self.report_data['user_analytics']['segment_analysis']
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Prepare data
            segments = list(segment_data.keys())
            sizes = [data['size'] for data in segment_data.values()]
            
            # Create bar plot
            plt.bar(segments, sizes)
            plt.title('User Segment Distribution')
            plt.xlabel('Segment')
            plt.ylabel('Number of Users')
            plt.xticks(rotation=45)
            
            # Save plot
            plt.tight_layout()
            plt.savefig(Path(output_dir) / 'user_segments.png')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting user segments: {str(e)}")
    
    def _plot_retention_heatmap(self, output_dir: str) -> None:
        """Create retention heatmap visualization."""
        try:
            if 'cohort_analysis' not in self.report_data:
                return
            
            retention_data = self.report_data['cohort_analysis']['retention_analysis']['retention_by_cohort']
            
            # Convert to DataFrame
            retention_df = pd.DataFrame(retention_data)
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create heatmap
            sns.heatmap(retention_df, annot=True, fmt='.2f', cmap='YlOrRd')
            plt.title('Cohort Retention Heatmap')
            plt.xlabel('Period')
            plt.ylabel('Cohort')
            
            # Save plot
            plt.tight_layout()
            plt.savefig(Path(output_dir) / 'retention_heatmap.png')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting retention heatmap: {str(e)}")
    
    def _plot_engagement_trends(self, output_dir: str) -> None:
        """Create visualization for engagement trends."""
        try:
            if 'user_analytics' not in self.report_data:
                return
            
            engagement_data = self.report_data['user_analytics']['engagement_trends']['segment_comparison']
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            # Prepare data
            segments = list(engagement_data.keys())
            scores = [data['average_score'] for data in engagement_data.values()]
            
            # Create line plot
            plt.plot(segments, scores, marker='o')
            plt.title('Engagement Trends by Segment')
            plt.xlabel('Segment')
            plt.ylabel('Average Engagement Score')
            plt.xticks(rotation=45)
            
            # Save plot
            plt.tight_layout()
            plt.savefig(Path(output_dir) / 'engagement_trends.png')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting engagement trends: {str(e)}")
    
    def _plot_recommendation_performance(self, output_dir: str) -> None:
        """Create visualization for recommendation performance metrics."""
        try:
            if 'recommendation_metrics' not in self.report_data:
                return
            
            accuracy_data = self.report_data['recommendation_metrics']['accuracy_metrics']
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Prepare data
            metrics = ['precision', 'recall', 'ndcg']
            k_values = list(accuracy_data['precision'].keys())
            
            # Plot lines for each metric
            for metric in metrics:
                values = [accuracy_data[metric][k] for k in k_values]
                plt.plot(k_values, values, marker='o', label=metric.upper())
            
            plt.title('Recommendation Performance Metrics')
            plt.xlabel('K')
            plt.ylabel('Score')
            plt.legend()
            plt.grid(True)
            
            # Save plot
            plt.tight_layout()
            plt.savefig(Path(output_dir) / 'recommendation_performance.png')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting recommendation performance: {str(e)}")
    
    def _save_report_data(self, output_dir: str) -> None:
        """Save report data as JSON."""
        try:
            report_path = Path(output_dir) / f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convert numpy types to Python native types
            report_data = self._convert_to_serializable(self.report_data)
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving report data: {str(e)}")
    
    def _convert_to_serializable(self, obj: Any) -> Any:
        """Convert numpy types to Python native types for JSON serialization."""
        try:
            if isinstance(obj, dict):
                return {key: self._convert_to_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [self._convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32,
                               np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            return obj
            
        except Exception as e:
            logger.error(f"Error converting to serializable: {str(e)}")
            return None