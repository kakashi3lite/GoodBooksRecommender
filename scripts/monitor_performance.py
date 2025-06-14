import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple

from src.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.config = Config()
        self.model_dir = Path(self.config.MODEL_DIR)
        self.reports_dir = Path(self.config.REPORTS_DIR)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def load_metrics_history(self) -> List[Dict]:
        """Load metrics from all saved model versions."""
        try:
            metrics_files = list(self.model_dir.glob('metrics_*.json'))
            metrics_history = []
            
            for file_path in metrics_files:
                with open(file_path, 'r') as f:
                    metrics_data = json.load(f)
                    metrics_history.append(metrics_data)
            
            # Sort by timestamp
            metrics_history.sort(key=lambda x: x['timestamp'])
            return metrics_history
            
        except Exception as e:
            logger.error(f"Error loading metrics history: {str(e)}")
            return []
    
    def plot_metric_trends(self, metrics_history: List[Dict]) -> None:
        """Plot trends of different metrics over time."""
        try:
            timestamps = [m['timestamp'] for m in metrics_history]
            metrics_df = pd.DataFrame([
                {
                    'timestamp': m['timestamp'],
                    'rmse': m['metrics']['rmse'],
                    'mae': m['metrics']['mae'],
                    'mse': m['metrics']['mse']
                } for m in metrics_history
            ])
            
            # Create trend plots
            plt.figure(figsize=(12, 6))
            plt.plot(metrics_df['timestamp'], metrics_df['rmse'], label='RMSE')
            plt.plot(metrics_df['timestamp'], metrics_df['mae'], label='MAE')
            plt.plot(metrics_df['timestamp'], metrics_df['mse'], label='MSE')
            
            plt.title('Model Performance Metrics Over Time')
            plt.xlabel('Model Version')
            plt.ylabel('Error')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save plot
            plot_path = self.reports_dir / f'metric_trends_{datetime.now().strftime("%Y%m%d")}.png'
            plt.savefig(plot_path)
            plt.close()
            
            logger.info(f"Metric trends plot saved to {plot_path}")
            
        except Exception as e:
            logger.error(f"Error plotting metric trends: {str(e)}")
    
    def analyze_performance_drift(self, metrics_history: List[Dict]) -> Dict:
        """Analyze performance drift between model versions."""
        try:
            if len(metrics_history) < 2:
                return {'status': 'Not enough data for drift analysis'}
            
            latest = metrics_history[-1]['metrics']
            previous = metrics_history[-2]['metrics']
            
            # Calculate percentage changes
            changes = {}
            for metric in ['rmse', 'mae', 'mse']:
                pct_change = ((latest[metric] - previous[metric]) / previous[metric]) * 100
                changes[metric] = {
                    'previous': previous[metric],
                    'current': latest[metric],
                    'pct_change': pct_change,
                    'status': 'improved' if pct_change < 0 else 'degraded'
                }
            
            return changes
            
        except Exception as e:
            logger.error(f"Error analyzing performance drift: {str(e)}")
            return {}
    
    def generate_performance_report(self) -> None:
        """Generate a comprehensive performance report."""
        try:
            # Load metrics history
            metrics_history = self.load_metrics_history()
            if not metrics_history:
                logger.warning("No metrics history found")
                return
            
            # Analyze performance drift
            drift_analysis = self.analyze_performance_drift(metrics_history)
            
            # Generate plots
            self.plot_metric_trends(metrics_history)
            
            # Create report
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_versions': len(metrics_history),
                'latest_metrics': metrics_history[-1]['metrics'],
                'performance_drift': drift_analysis,
                'training_config': metrics_history[-1]['config']
            }
            
            # Save report
            report_path = self.reports_dir / f'performance_report_{datetime.now().strftime("%Y%m%d")}.json'
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Performance report generated and saved to {report_path}")
            
            # Log summary
            self._log_report_summary(report)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
    
    def _log_report_summary(self, report: Dict) -> None:
        """Log a summary of the performance report."""
        try:
            logger.info("\nPerformance Report Summary:")
            logger.info(f"Total model versions: {report['total_versions']}")
            logger.info("\nLatest Metrics:")
            for metric, value in report['latest_metrics'].items():
                logger.info(f"{metric.upper()}: {value:.4f}")
            
            if 'performance_drift' in report and isinstance(report['performance_drift'], dict):
                logger.info("\nPerformance Drift Analysis:")
                for metric, data in report['performance_drift'].items():
                    if isinstance(data, dict) and 'pct_change' in data:
                        logger.info(
                            f"{metric.upper()}: {data['pct_change']:.2f}% ({data['status']})"
                        )
            
        except Exception as e:
            logger.error(f"Error logging report summary: {str(e)}")

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.generate_performance_report()