import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict
from src.config import Config
from src.user.interaction_tracker import InteractionTracker

logger = logging.getLogger(__name__)

class CohortAnalysis:
    def __init__(self, config: Config, interaction_tracker: InteractionTracker):
        self.config = config
        self.interaction_tracker = interaction_tracker
        self.cohort_data: Dict[str, pd.DataFrame] = {}
        self.retention_matrices: Dict[str, pd.DataFrame] = {}
        self.engagement_matrices: Dict[str, pd.DataFrame] = {}
        
    def analyze_cohorts(self, 
                       time_window: Optional[timedelta] = None,
                       min_cohort_size: int = 50) -> Dict[str, Any]:
        """Perform comprehensive cohort analysis."""
        try:
            # Get user interaction data
            interactions = self._prepare_interaction_data(time_window)
            if interactions.empty:
                return {}
            
            # Create cohorts
            cohorts = self._create_cohorts(interactions)
            
            # Filter small cohorts
            valid_cohorts = self._filter_cohorts(cohorts, min_cohort_size)
            
            # Calculate metrics
            analysis = {
                'retention': self._calculate_retention_metrics(valid_cohorts),
                'engagement': self._calculate_engagement_metrics(valid_cohorts),
                'lifetime_value': self._calculate_ltv_metrics(valid_cohorts),
                'behavior_patterns': self._analyze_cohort_behaviors(valid_cohorts),
                'summary': self._generate_cohort_summary(valid_cohorts)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing cohort analysis: {str(e)}")
            raise
    
    def _prepare_interaction_data(self, time_window: Optional[timedelta]) -> pd.DataFrame:
        """Prepare interaction data for cohort analysis."""
        try:
            # Get all interactions
            interactions = []
            for user_id, user_interactions in self.interaction_tracker.interactions.items():
                for interaction in user_interactions:
                    interaction_data = {
                        'user_id': user_id,
                        'timestamp': interaction['timestamp'],
                        'type': interaction['type'],
                        'engagement_score': interaction['metadata'].get('engagement_score', 0),
                        'value': interaction['metadata'].get('value', 0)
                    }
                    interactions.append(interaction_data)
            
            if not interactions:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(interactions)
            
            # Filter by time window if specified
            if time_window:
                cutoff_time = datetime.now() - time_window
                df = df[df['timestamp'] >= cutoff_time]
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing interaction data: {str(e)}")
            return pd.DataFrame()
    
    def _create_cohorts(self, interactions: pd.DataFrame) -> pd.DataFrame:
        """Create user cohorts based on first interaction date."""
        try:
            # Get first interaction date for each user
            first_interactions = interactions.groupby('user_id')['timestamp'].min().reset_index()
            first_interactions['cohort_date'] = first_interactions['timestamp'].dt.to_period('M')
            
            # Merge cohort information back to interactions
            cohorts = interactions.merge(
                first_interactions[['user_id', 'cohort_date']],
                on='user_id',
                how='left'
            )
            
            # Calculate periods since first interaction
            cohorts['period_number'] = (
                cohorts['timestamp'].dt.to_period('M') - 
                cohorts['cohort_date']
            ).apply(lambda x: x.n)
            
            return cohorts
            
        except Exception as e:
            logger.error(f"Error creating cohorts: {str(e)}")
            raise
    
    def _filter_cohorts(self, 
                        cohorts: pd.DataFrame, 
                        min_size: int) -> pd.DataFrame:
        """Filter cohorts based on minimum size requirement."""
        try:
            # Count users per cohort
            cohort_sizes = cohorts.groupby('cohort_date')['user_id'].nunique()
            
            # Get valid cohorts
            valid_cohorts = cohort_sizes[cohort_sizes >= min_size].index
            
            # Filter dataframe
            filtered_cohorts = cohorts[cohorts['cohort_date'].isin(valid_cohorts)]
            
            return filtered_cohorts
            
        except Exception as e:
            logger.error(f"Error filtering cohorts: {str(e)}")
            raise
    
    def _calculate_retention_metrics(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Calculate retention metrics for each cohort."""
        try:
            # Calculate retention matrix
            retention_matrix = self._create_retention_matrix(cohorts)
            
            # Calculate retention metrics
            metrics = {
                'retention_matrix': retention_matrix.to_dict(),
                'average_retention': self._calculate_average_retention(retention_matrix),
                'retention_trends': self._analyze_retention_trends(retention_matrix)
            }
            
            # Store for later use
            self.retention_matrices[datetime.now().strftime('%Y-%m')] = retention_matrix
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating retention metrics: {str(e)}")
            raise
    
    def _create_retention_matrix(self, cohorts: pd.DataFrame) -> pd.DataFrame:
        """Create retention matrix showing user retention over time."""
        try:
            # Count unique users for each cohort and period
            retention_data = cohorts.groupby(['cohort_date', 'period_number'])['user_id'].nunique()
            
            # Reshape into matrix form
            retention_matrix = retention_data.unstack()
            
            # Calculate retention percentages
            for column in retention_matrix.columns:
                retention_matrix[column] = retention_matrix[column] / retention_matrix[0]
            
            return retention_matrix
            
        except Exception as e:
            logger.error(f"Error creating retention matrix: {str(e)}")
            raise
    
    def _calculate_average_retention(self, retention_matrix: pd.DataFrame) -> Dict[int, float]:
        """Calculate average retention rates for each period."""
        try:
            return retention_matrix.mean().to_dict()
            
        except Exception as e:
            logger.error(f"Error calculating average retention: {str(e)}")
            return {}
    
    def _analyze_retention_trends(self, retention_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in retention rates."""
        try:
            trends = {
                'early_drop': float(1 - retention_matrix[1].mean()),
                'long_term': float(retention_matrix[retention_matrix.columns[-1]].mean()),
                'stability': self._calculate_retention_stability(retention_matrix)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing retention trends: {str(e)}")
            return {}
    
    def _calculate_retention_stability(self, retention_matrix: pd.DataFrame) -> float:
        """Calculate stability score for retention rates."""
        try:
            # Calculate variance in retention drop between periods
            retention_changes = retention_matrix.diff(axis=1).mean()
            stability = 1 / (1 + np.std(retention_changes))
            
            return float(stability)
            
        except Exception as e:
            logger.error(f"Error calculating retention stability: {str(e)}")
            return 0.0
    
    def _calculate_engagement_metrics(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Calculate engagement metrics for each cohort."""
        try:
            # Create engagement matrix
            engagement_matrix = self._create_engagement_matrix(cohorts)
            
            metrics = {
                'engagement_matrix': engagement_matrix.to_dict(),
                'average_engagement': self._calculate_average_engagement(engagement_matrix),
                'engagement_trends': self._analyze_engagement_trends(engagement_matrix)
            }
            
            # Store for later use
            self.engagement_matrices[datetime.now().strftime('%Y-%m')] = engagement_matrix
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {str(e)}")
            raise
    
    def _create_engagement_matrix(self, cohorts: pd.DataFrame) -> pd.DataFrame:
        """Create matrix showing average engagement scores over time."""
        try:
            engagement_data = cohorts.groupby(['cohort_date', 'period_number'])['engagement_score'].mean()
            return engagement_data.unstack()
            
        except Exception as e:
            logger.error(f"Error creating engagement matrix: {str(e)}")
            raise
    
    def _calculate_average_engagement(self, engagement_matrix: pd.DataFrame) -> Dict[int, float]:
        """Calculate average engagement for each period."""
        try:
            return engagement_matrix.mean().to_dict()
            
        except Exception as e:
            logger.error(f"Error calculating average engagement: {str(e)}")
            return {}
    
    def _analyze_engagement_trends(self, engagement_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in engagement levels."""
        try:
            trends = {
                'initial_engagement': float(engagement_matrix[0].mean()),
                'trend_slope': self._calculate_trend_slope(engagement_matrix),
                'volatility': float(engagement_matrix.std().mean())
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {str(e)}")
            return {}
    
    def _calculate_trend_slope(self, matrix: pd.DataFrame) -> float:
        """Calculate the overall trend slope."""
        try:
            # Use simple linear regression
            x = np.arange(len(matrix.columns))
            y = matrix.mean()
            
            slope = np.polyfit(x, y, 1)[0]
            return float(slope)
            
        except Exception as e:
            logger.error(f"Error calculating trend slope: {str(e)}")
            return 0.0
    
    def _calculate_ltv_metrics(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Calculate lifetime value metrics for cohorts."""
        try:
            # Calculate cumulative value per user
            ltv_data = cohorts.groupby(['cohort_date', 'user_id'])['value'].sum()
            
            metrics = {
                'average_ltv': float(ltv_data.mean()),
                'ltv_by_cohort': ltv_data.groupby('cohort_date').mean().to_dict(),
                'ltv_distribution': self._calculate_ltv_distribution(ltv_data)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating LTV metrics: {str(e)}")
            raise
    
    def _calculate_ltv_distribution(self, ltv_data: pd.Series) -> Dict[str, float]:
        """Calculate distribution statistics for lifetime values."""
        try:
            distribution = {
                'mean': float(ltv_data.mean()),
                'median': float(ltv_data.median()),
                'std': float(ltv_data.std()),
                'percentiles': {
                    '25': float(ltv_data.quantile(0.25)),
                    '75': float(ltv_data.quantile(0.75)),
                    '90': float(ltv_data.quantile(0.90))
                }
            }
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error calculating LTV distribution: {str(e)}")
            return {}
    
    def _analyze_cohort_behaviors(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze behavioral patterns within cohorts."""
        try:
            behaviors = {
                'interaction_types': self._analyze_interaction_types(cohorts),
                'activity_patterns': self._analyze_activity_patterns(cohorts),
                'value_patterns': self._analyze_value_patterns(cohorts)
            }
            
            return behaviors
            
        except Exception as e:
            logger.error(f"Error analyzing cohort behaviors: {str(e)}")
            raise
    
    def _analyze_interaction_types(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution of interaction types."""
        try:
            type_dist = cohorts.groupby(['cohort_date', 'type']).size().unstack(fill_value=0)
            
            # Calculate percentages
            type_dist_pct = type_dist.div(type_dist.sum(axis=1), axis=0)
            
            return {
                'distribution': type_dist.to_dict(),
                'percentages': type_dist_pct.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing interaction types: {str(e)}")
            return {}
    
    def _analyze_activity_patterns(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in activity timing and frequency."""
        try:
            # Add time-based features
            cohorts['hour'] = cohorts['timestamp'].dt.hour
            cohorts['day_of_week'] = cohorts['timestamp'].dt.dayofweek
            
            patterns = {
                'hourly_distribution': cohorts.groupby('hour').size().to_dict(),
                'daily_distribution': cohorts.groupby('day_of_week').size().to_dict(),
                'activity_frequency': self._calculate_activity_frequency(cohorts)
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing activity patterns: {str(e)}")
            return {}
    
    def _calculate_activity_frequency(self, cohorts: pd.DataFrame) -> Dict[str, float]:
        """Calculate frequency metrics for user activity."""
        try:
            # Calculate average time between interactions
            frequency = cohorts.groupby('user_id')['timestamp'].agg(lambda x: np.mean(np.diff(x.sort_values())))
            
            metrics = {
                'mean_interval': float(frequency.mean().total_seconds() / 3600),  # in hours
                'median_interval': float(frequency.median().total_seconds() / 3600),
                'std_interval': float(frequency.std().total_seconds() / 3600)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating activity frequency: {str(e)}")
            return {}
    
    def _analyze_value_patterns(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in value generation."""
        try:
            value_patterns = {
                'value_progression': self._analyze_value_progression(cohorts),
                'value_distribution': self._analyze_value_distribution(cohorts)
            }
            
            return value_patterns
            
        except Exception as e:
            logger.error(f"Error analyzing value patterns: {str(e)}")
            return {}
    
    def _analyze_value_progression(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how value generation progresses over time."""
        try:
            # Calculate cumulative value by period
            value_prog = cohorts.groupby(['cohort_date', 'period_number'])['value'].sum()
            value_matrix = value_prog.unstack(fill_value=0)
            
            # Calculate growth rates
            growth_rates = value_matrix.pct_change(axis=1)
            
            return {
                'cumulative_value': value_matrix.to_dict(),
                'growth_rates': growth_rates.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing value progression: {str(e)}")
            return {}
    
    def _analyze_value_distribution(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the distribution of value across users."""
        try:
            user_values = cohorts.groupby('user_id')['value'].sum()
            
            distribution = {
                'mean': float(user_values.mean()),
                'median': float(user_values.median()),
                'std': float(user_values.std()),
                'percentiles': {
                    str(p): float(user_values.quantile(p/100))
                    for p in [25, 50, 75, 90, 95, 99]
                }
            }
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error analyzing value distribution: {str(e)}")
            return {}
    
    def _generate_cohort_summary(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics and insights for cohorts."""
        try:
            summary = {
                'total_cohorts': len(cohorts['cohort_date'].unique()),
                'total_users': len(cohorts['user_id'].unique()),
                'total_interactions': len(cohorts),
                'cohort_sizes': cohorts.groupby('cohort_date')['user_id'].nunique().to_dict(),
                'key_metrics': self._calculate_key_metrics(cohorts),
                'trends': self._identify_key_trends(cohorts)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating cohort summary: {str(e)}")
            raise
    
    def _calculate_key_metrics(self, cohorts: pd.DataFrame) -> Dict[str, float]:
        """Calculate key performance metrics across all cohorts."""
        try:
            metrics = {
                'average_engagement': float(cohorts['engagement_score'].mean()),
                'average_value': float(cohorts['value'].mean()),
                'interaction_rate': float(len(cohorts) / len(cohorts['user_id'].unique())),
                'retention_rate': self._calculate_overall_retention(cohorts)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating key metrics: {str(e)}")
            return {}
    
    def _calculate_overall_retention(self, cohorts: pd.DataFrame) -> float:
        """Calculate overall retention rate across all cohorts."""
        try:
            # Count users who have interactions beyond their first period
            total_users = len(cohorts['user_id'].unique())
            retained_users = len(cohorts[cohorts['period_number'] > 0]['user_id'].unique())
            
            return float(retained_users / total_users if total_users > 0 else 0)
            
        except Exception as e:
            logger.error(f"Error calculating overall retention: {str(e)}")
            return 0.0
    
    def _identify_key_trends(self, cohorts: pd.DataFrame) -> Dict[str, Any]:
        """Identify key trends and patterns in the cohort data."""
        try:
            # Analyze trends over time
            trends = {
                'engagement_trend': self._calculate_trend_slope(cohorts.groupby('cohort_date')['engagement_score'].mean()),
                'value_trend': self._calculate_trend_slope(cohorts.groupby('cohort_date')['value'].mean()),
                'cohort_growth': self._calculate_cohort_growth(cohorts)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error identifying key trends: {str(e)}")
            return {}
    
    def _calculate_cohort_growth(self, cohorts: pd.DataFrame) -> float:
        """Calculate growth rate in cohort sizes."""
        try:
            cohort_sizes = cohorts.groupby('cohort_date')['user_id'].nunique()
            if len(cohort_sizes) < 2:
                return 0.0
            
            growth_rates = cohort_sizes.pct_change()
            return float(growth_rates.mean())
            
        except Exception as e:
            logger.error(f"Error calculating cohort growth: {str(e)}")
            return 0.0