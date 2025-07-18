"""
AI-Powered Send Time Optimizer
Predicts optimal send times for maximum engagement using ML models.
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import pytz
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.newsletter.core.personalization_engine import UserPersona


class TimeZone(Enum):
    """Supported time zones"""
    UTC = "UTC"
    EST = "America/New_York"
    PST = "America/Los_Angeles"
    GMT = "Europe/London"
    CET = "Europe/Paris"
    JST = "Asia/Tokyo"
    AEST = "Australia/Sydney"


class SendTimeStrategy(Enum):
    """Send time optimization strategies"""
    IMMEDIATE = "immediate"
    OPTIMAL_PERSONAL = "optimal_personal"
    OPTIMAL_GLOBAL = "optimal_global"
    COHORT_BASED = "cohort_based"
    A_B_TEST = "a_b_test"


@dataclass
class SendTimeCandidate:
    """Candidate send time with predictions"""
    send_time: datetime
    predicted_engagement: float
    confidence_score: float
    reasoning: List[str]
    time_zone: str
    local_time: str
    day_of_week: str
    is_weekend: bool
    is_holiday: bool = False


@dataclass
class SendTimeAnalytics:
    """Analytics for send time optimization"""
    user_id: str
    optimal_send_times: List[SendTimeCandidate]
    historical_performance: Dict[str, float]
    time_zone_distribution: Dict[str, int]
    engagement_patterns: Dict[str, Any]
    cohort_insights: Dict[str, Any]
    last_updated: datetime = field(default_factory=datetime.utcnow)


class SendTimeOptimizer:
    """
    AI-Powered Send Time Optimizer
    
    Features:
    - Individual user send time optimization
    - Cohort-based analysis
    - Global engagement pattern analysis
    - Time zone intelligence
    - Holiday and event awareness
    - A/B testing for send time strategies
    """
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        default_timezone: str = "UTC"
    ):
        self.cache = cache_manager
        self.default_timezone = default_timezone
        self.logger = StructuredLogger(__name__)
        
        # ML Models
        self.engagement_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.model_trained = False
        
        # Engagement patterns cache
        self.global_patterns: Dict[str, float] = {}
        self.cohort_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Holidays and special events (simplified)
        self.holidays = {
            "2024-01-01": "New Year",
            "2024-12-25": "Christmas",
            "2024-07-04": "Independence Day",
            "2024-11-28": "Thanksgiving"
        }
    
    async def find_optimal_send_time(
        self,
        user_persona: UserPersona,
        strategy: SendTimeStrategy = SendTimeStrategy.OPTIMAL_PERSONAL,
        target_date: Optional[datetime] = None
    ) -> SendTimeCandidate:
        """Find optimal send time for a user"""
        try:
            target_date = target_date or datetime.utcnow()
            
            # Get user timezone
            user_timezone = await self._get_user_timezone(user_persona.user_id)
            
            # Generate candidate send times
            candidates = await self._generate_send_time_candidates(
                user_persona, target_date, user_timezone, strategy
            )
            
            # Score and rank candidates
            scored_candidates = await self._score_send_time_candidates(
                candidates, user_persona, strategy
            )
            
            # Select optimal time
            optimal_candidate = await self._select_optimal_candidate(
                scored_candidates, user_persona, strategy
            )
            
            # Cache result
            cache_key = f"optimal_send_time:{user_persona.user_id}:{target_date.date()}"
            await self.cache.set(
                cache_key,
                json.dumps(optimal_candidate.__dict__, default=str),
                ttl=3600  # 1 hour cache
            )
            
            self.logger.info(
                "Optimal send time found",
                user_id=user_persona.user_id,
                send_time=optimal_candidate.send_time.isoformat(),
                predicted_engagement=optimal_candidate.predicted_engagement,
                strategy=strategy.value,
                local_time=optimal_candidate.local_time
            )
            
            return optimal_candidate
            
        except Exception as e:
            self.logger.error(
                "Send time optimization failed",
                user_id=user_persona.user_id,
                error=str(e)
            )
            # Return default send time
            return await self._get_default_send_time(user_persona, target_date)
    
    async def batch_optimize_send_times(
        self,
        user_personas: List[UserPersona],
        strategy: SendTimeStrategy = SendTimeStrategy.COHORT_BASED
    ) -> Dict[str, SendTimeCandidate]:
        """Optimize send times for multiple users"""
        try:
            optimization_tasks = [
                self.find_optimal_send_time(persona, strategy)
                for persona in user_personas
            ]
            
            results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
            
            optimized_times = {}
            successful_optimizations = 0
            
            for persona, result in zip(user_personas, results):
                if isinstance(result, Exception):
                    self.logger.warning(
                        "Individual optimization failed",
                        user_id=persona.user_id,
                        error=str(result)
                    )
                    # Use default time
                    result = await self._get_default_send_time(persona)
                else:
                    successful_optimizations += 1
                
                optimized_times[persona.user_id] = result
            
            self.logger.info(
                "Batch send time optimization completed",
                total_users=len(user_personas),
                successful_optimizations=successful_optimizations,
                strategy=strategy.value
            )
            
            return optimized_times
            
        except Exception as e:
            self.logger.error(
                "Batch send time optimization failed",
                error=str(e)
            )
            return {}
    
    async def analyze_send_time_performance(
        self,
        user_id: str,
        historical_data: List[Dict[str, Any]]
    ) -> SendTimeAnalytics:
        """Analyze historical send time performance"""
        try:
            # Process historical data
            df = pd.DataFrame(historical_data)
            
            if df.empty:
                return await self._create_default_analytics(user_id)
            
            # Extract time-based features
            df['hour'] = pd.to_datetime(df['sent_at']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['sent_at']).dt.day_name()
            df['is_weekend'] = pd.to_datetime(df['sent_at']).dt.weekday >= 5
            
            # Calculate performance metrics
            performance_by_hour = df.groupby('hour')['engagement_rate'].mean().to_dict()
            performance_by_day = df.groupby('day_of_week')['engagement_rate'].mean().to_dict()
            
            # Find optimal times
            best_hours = sorted(performance_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
            optimal_candidates = []
            
            for hour, engagement_rate in best_hours:
                candidate = SendTimeCandidate(
                    send_time=datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0),
                    predicted_engagement=engagement_rate,
                    confidence_score=min(1.0, len(df[df['hour'] == hour]) / 10.0),  # Based on data points
                    reasoning=[f"Historically performs {engagement_rate:.2%} engagement at {hour:02d}:00"],
                    time_zone=self.default_timezone,
                    local_time=f"{hour:02d}:00",
                    day_of_week="weekday" if hour not in [0, 1, 22, 23] else "any",
                    is_weekend=False
                )
                optimal_candidates.append(candidate)
            
            # Time zone analysis
            user_timezone = await self._get_user_timezone(user_id)
            timezone_dist = {user_timezone: len(df)}
            
            # Engagement patterns
            patterns = {
                "best_hour": max(performance_by_hour, key=performance_by_hour.get),
                "best_day": max(performance_by_day, key=performance_by_day.get),
                "weekend_vs_weekday": {
                    "weekend": df[df['is_weekend']]['engagement_rate'].mean(),
                    "weekday": df[~df['is_weekend']]['engagement_rate'].mean()
                },
                "hourly_performance": performance_by_hour,
                "daily_performance": performance_by_day
            }
            
            analytics = SendTimeAnalytics(
                user_id=user_id,
                optimal_send_times=optimal_candidates,
                historical_performance=patterns,
                time_zone_distribution=timezone_dist,
                engagement_patterns=patterns,
                cohort_insights=await self._get_cohort_insights(user_id)
            )
            
            self.logger.info(
                "Send time analytics generated",
                user_id=user_id,
                data_points=len(df),
                best_hour=patterns["best_hour"],
                best_day=patterns["best_day"]
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(
                "Send time analysis failed",
                user_id=user_id,
                error=str(e)
            )
            return await self._create_default_analytics(user_id)
    
    async def update_global_patterns(
        self,
        engagement_data: List[Dict[str, Any]]
    ) -> None:
        """Update global engagement patterns"""
        try:
            if not engagement_data:
                return
            
            df = pd.DataFrame(engagement_data)
            df['hour'] = pd.to_datetime(df['sent_at']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['sent_at']).dt.day_name()
            
            # Update global patterns
            self.global_patterns = {
                "hourly": df.groupby('hour')['engagement_rate'].mean().to_dict(),
                "daily": df.groupby('day_of_week')['engagement_rate'].mean().to_dict(),
                "overall_average": df['engagement_rate'].mean()
            }
            
            # Cache global patterns
            await self.cache.set(
                "global_send_time_patterns",
                json.dumps(self.global_patterns, default=str),
                ttl=86400  # 24 hours
            )
            
            self.logger.info(
                "Global patterns updated",
                data_points=len(df),
                avg_engagement=self.global_patterns["overall_average"]
            )
            
        except Exception as e:
            self.logger.error(
                "Global pattern update failed",
                error=str(e)
            )
    
    async def train_engagement_model(
        self,
        training_data: List[Dict[str, Any]]
    ) -> bool:
        """Train ML model for engagement prediction"""
        try:
            if len(training_data) < 100:  # Minimum data requirement
                self.logger.warning(
                    "Insufficient training data for ML model",
                    data_points=len(training_data)
                )
                return False
            
            df = pd.DataFrame(training_data)
            
            # Feature engineering
            df['hour'] = pd.to_datetime(df['sent_at']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['sent_at']).dt.weekday
            df['is_weekend'] = df['day_of_week'] >= 5
            df['month'] = pd.to_datetime(df['sent_at']).dt.month
            
            # Prepare features
            features = ['hour', 'day_of_week', 'is_weekend', 'month']
            X = df[features]
            y = df['engagement_rate']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.engagement_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_score = self.engagement_model.score(X_train_scaled, y_train)
            test_score = self.engagement_model.score(X_test_scaled, y_test)
            
            self.model_trained = True
            
            self.logger.info(
                "Engagement model trained",
                training_samples=len(X_train),
                test_samples=len(X_test),
                train_score=train_score,
                test_score=test_score
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Model training failed",
                error=str(e)
            )
            return False
    
    # Private helper methods
    
    async def _generate_send_time_candidates(
        self,
        user_persona: UserPersona,
        target_date: datetime,
        user_timezone: str,
        strategy: SendTimeStrategy
    ) -> List[SendTimeCandidate]:
        """Generate candidate send times"""
        candidates = []
        
        # Get user's preferred times from persona
        preferred_hours = [int(t.split(':')[0]) for t in user_persona.reading_times]
        
        if strategy == SendTimeStrategy.IMMEDIATE:
            # Only current time
            candidates.append(await self._create_candidate(target_date, user_timezone))
        
        elif strategy == SendTimeStrategy.OPTIMAL_PERSONAL:
            # User's preferred times + slight variations
            for hour in preferred_hours:
                for day_offset in [0, 1]:  # Today and tomorrow
                    candidate_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    candidate_time += timedelta(days=day_offset)
                    candidates.append(await self._create_candidate(candidate_time, user_timezone))
        
        elif strategy == SendTimeStrategy.OPTIMAL_GLOBAL:
            # Best global times
            global_patterns = await self._get_global_patterns()
            best_hours = sorted(
                global_patterns.get("hourly", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for hour, _ in best_hours:
                candidate_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                candidates.append(await self._create_candidate(candidate_time, user_timezone))
        
        elif strategy == SendTimeStrategy.COHORT_BASED:
            # Cohort-based optimization
            cohort_times = await self._get_cohort_optimal_times(user_persona)
            for hour in cohort_times[:3]:
                candidate_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                candidates.append(await self._create_candidate(candidate_time, user_timezone))
        
        elif strategy == SendTimeStrategy.A_B_TEST:
            # A/B test candidates
            test_hours = [8, 12, 18, 20]  # Morning, noon, evening, night
            for hour in test_hours:
                candidate_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                candidates.append(await self._create_candidate(candidate_time, user_timezone))
        
        return candidates
    
    async def _create_candidate(
        self,
        send_time: datetime,
        user_timezone: str
    ) -> SendTimeCandidate:
        """Create a send time candidate"""
        # Convert to user timezone
        utc_tz = pytz.UTC
        user_tz = pytz.timezone(user_timezone)
        
        if send_time.tzinfo is None:
            send_time = utc_tz.localize(send_time)
        
        local_time = send_time.astimezone(user_tz)
        
        is_holiday = send_time.date().strftime("%Y-%m-%d") in self.holidays
        
        return SendTimeCandidate(
            send_time=send_time,
            predicted_engagement=0.5,  # Will be calculated later
            confidence_score=0.5,
            reasoning=[],
            time_zone=user_timezone,
            local_time=local_time.strftime("%H:%M"),
            day_of_week=local_time.strftime("%A"),
            is_weekend=local_time.weekday() >= 5,
            is_holiday=is_holiday
        )
    
    async def _score_send_time_candidates(
        self,
        candidates: List[SendTimeCandidate],
        user_persona: UserPersona,
        strategy: SendTimeStrategy
    ) -> List[SendTimeCandidate]:
        """Score and rank send time candidates"""
        for candidate in candidates:
            score = await self._calculate_engagement_score(candidate, user_persona, strategy)
            candidate.predicted_engagement = score
            candidate.reasoning = await self._generate_reasoning(candidate, user_persona, score)
            candidate.confidence_score = await self._calculate_confidence(candidate, user_persona)
        
        return sorted(candidates, key=lambda x: x.predicted_engagement, reverse=True)
    
    async def _calculate_engagement_score(
        self,
        candidate: SendTimeCandidate,
        user_persona: UserPersona,
        strategy: SendTimeStrategy
    ) -> float:
        """Calculate predicted engagement score"""
        if self.model_trained:
            # Use trained ML model
            features = np.array([[
                candidate.send_time.hour,
                candidate.send_time.weekday(),
                1 if candidate.is_weekend else 0,
                candidate.send_time.month
            ]])
            
            features_scaled = self.scaler.transform(features)
            predicted_score = self.engagement_model.predict(features_scaled)[0]
            return max(0.0, min(1.0, predicted_score))
        
        # Fallback to heuristic scoring
        base_score = 0.3
        
        # Hour-based scoring
        hour = candidate.send_time.hour
        if 8 <= hour <= 10:  # Morning peak
            base_score += 0.2
        elif 18 <= hour <= 20:  # Evening peak
            base_score += 0.3
        elif 12 <= hour <= 14:  # Lunch time
            base_score += 0.1
        elif hour < 6 or hour > 23:  # Very early/late
            base_score -= 0.2
        
        # User preference alignment
        preferred_hours = [int(t.split(':')[0]) for t in user_persona.reading_times]
        if hour in preferred_hours:
            base_score += 0.2
        
        # Engagement pattern alignment
        if user_persona.engagement_pattern == "morning" and 6 <= hour <= 12:
            base_score += 0.1
        elif user_persona.engagement_pattern == "evening" and 17 <= hour <= 23:
            base_score += 0.1
        
        # Weekend adjustment
        if candidate.is_weekend:
            base_score += 0.05  # Slight weekend boost
        
        # Holiday penalty
        if candidate.is_holiday:
            base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    async def _generate_reasoning(
        self,
        candidate: SendTimeCandidate,
        user_persona: UserPersona,
        score: float
    ) -> List[str]:
        """Generate reasoning for the send time score"""
        reasons = []
        
        if score > 0.7:
            reasons.append("High engagement expected")
        elif score > 0.5:
            reasons.append("Good engagement expected")
        else:
            reasons.append("Lower engagement expected")
        
        hour = candidate.send_time.hour
        if 8 <= hour <= 10:
            reasons.append("Morning peak hours")
        elif 18 <= hour <= 20:
            reasons.append("Evening peak hours")
        
        preferred_hours = [int(t.split(':')[0]) for t in user_persona.reading_times]
        if hour in preferred_hours:
            reasons.append("Matches your preferred reading time")
        
        if user_persona.engagement_pattern == "morning" and 6 <= hour <= 12:
            reasons.append("Aligns with your morning engagement pattern")
        elif user_persona.engagement_pattern == "evening" and 17 <= hour <= 23:
            reasons.append("Aligns with your evening engagement pattern")
        
        if candidate.is_weekend:
            reasons.append("Weekend timing for relaxed reading")
        
        if candidate.is_holiday:
            reasons.append("Holiday timing - may have lower engagement")
        
        return reasons
    
    async def _calculate_confidence(
        self,
        candidate: SendTimeCandidate,
        user_persona: UserPersona
    ) -> float:
        """Calculate confidence in the prediction"""
        confidence = 0.5
        
        # More confidence if we have user interaction history
        if len(user_persona.interaction_history) > 10:
            confidence += 0.2
        
        # More confidence if it's a typical time
        hour = candidate.send_time.hour
        if 8 <= hour <= 22:  # Normal waking hours
            confidence += 0.1
        
        # More confidence if it matches user patterns
        preferred_hours = [int(t.split(':')[0]) for t in user_persona.reading_times]
        if hour in preferred_hours:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    async def _select_optimal_candidate(
        self,
        candidates: List[SendTimeCandidate],
        user_persona: UserPersona,
        strategy: SendTimeStrategy
    ) -> SendTimeCandidate:
        """Select the optimal candidate"""
        if not candidates:
            return await self._get_default_send_time(user_persona)
        
        # For A/B testing, randomly select from top candidates
        if strategy == SendTimeStrategy.A_B_TEST and len(candidates) >= 2:
            import random
            return random.choice(candidates[:2])
        
        # Otherwise, return the top candidate
        return candidates[0]
    
    async def _get_default_send_time(
        self,
        user_persona: UserPersona,
        target_date: Optional[datetime] = None
    ) -> SendTimeCandidate:
        """Get default send time"""
        target_date = target_date or datetime.utcnow()
        user_timezone = await self._get_user_timezone(user_persona.user_id)
        
        # Default to user's first preferred time or 9 AM
        if user_persona.reading_times:
            hour = int(user_persona.reading_times[0].split(':')[0])
        else:
            hour = 9
        
        default_time = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        return await self._create_candidate(default_time, user_timezone)
    
    async def _get_user_timezone(self, user_id: str) -> str:
        """Get user's timezone"""
        # This would fetch from user preferences in database
        # For now, return default
        return self.default_timezone
    
    async def _get_global_patterns(self) -> Dict[str, Any]:
        """Get global engagement patterns"""
        cached_patterns = await self.cache.get("global_send_time_patterns")
        if cached_patterns:
            return json.loads(cached_patterns)
        
        # Default patterns if no cache
        return {
            "hourly": {
                "6": 0.2, "7": 0.3, "8": 0.5, "9": 0.6, "10": 0.4,
                "11": 0.3, "12": 0.4, "13": 0.3, "14": 0.3, "15": 0.3,
                "16": 0.4, "17": 0.5, "18": 0.7, "19": 0.8, "20": 0.7,
                "21": 0.5, "22": 0.3, "23": 0.2
            },
            "daily": {
                "Monday": 0.5, "Tuesday": 0.6, "Wednesday": 0.6,
                "Thursday": 0.6, "Friday": 0.5, "Saturday": 0.4, "Sunday": 0.4
            },
            "overall_average": 0.45
        }
    
    async def _get_cohort_optimal_times(self, user_persona: UserPersona) -> List[int]:
        """Get optimal times for user's cohort"""
        # Simplified cohort analysis
        if "avid_reader" in user_persona.behavioral_clusters:
            return [19, 20, 21]  # Evening readers
        elif "morning_person" in user_persona.behavioral_clusters:
            return [7, 8, 9]  # Morning readers
        else:
            return [18, 19, 20]  # General optimal times
    
    async def _get_cohort_insights(self, user_id: str) -> Dict[str, Any]:
        """Get cohort-specific insights"""
        return {
            "cohort_type": "avid_reader",
            "avg_optimal_hour": 19,
            "weekend_preference": "later_hours",
            "engagement_boost": 1.2
        }
    
    async def _create_default_analytics(self, user_id: str) -> SendTimeAnalytics:
        """Create default analytics for new users"""
        default_candidate = SendTimeCandidate(
            send_time=datetime.utcnow().replace(hour=19, minute=0, second=0, microsecond=0),
            predicted_engagement=0.5,
            confidence_score=0.3,
            reasoning=["Default evening time"],
            time_zone=self.default_timezone,
            local_time="19:00",
            day_of_week="Any",
            is_weekend=False
        )
        
        return SendTimeAnalytics(
            user_id=user_id,
            optimal_send_times=[default_candidate],
            historical_performance={"overall": 0.5},
            time_zone_distribution={self.default_timezone: 1},
            engagement_patterns={"default": True},
            cohort_insights={"type": "new_user"}
        )
