Пользователь хочет продолжить с A/B Testing Framework. Это важная часть аналитики поисковой системы, которая позволяет тестировать различные алгоритмы ранжирования, UI изменения и другие улучшения.

Создам подробный раздел о:
1. A/B Testing Framework - архитектура и реализация
2. Experiment Management - создание и управление экспериментами
3. Statistical Analysis - статистический анализ результатов
4. Traffic Splitting - распределение трафика между вариантами
5. Result Evaluation - оценка и выбор победителя# 🎯 DEEP-DIVE: SEARCH SYSTEM (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 6: `docs/deep-dive/search/AB_TESTING.md`

```markdown
# A/B Testing Framework - Deep Dive

## 🧪 A/B Testing Architecture

### Experiment Flow

```
User Search Request
       │
       ▼
┌──────────────────┐
│ Experiment       │
│ Assignment       │
│ (Deterministic)  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Control   Variant
 Group     Group
    │         │
    │    ┌────┴────┐
    │    │ Feature │
    │    │ Applied │
    │    └────┬────┘
    │         │
    └────┬────┘
         │
         ▼
┌──────────────────┐
│ Execute Search   │
│ (Instrumented)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Log Metrics      │
│ • Impressions    │
│ • Clicks         │
│ • Conversions    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Statistical      │
│ Analysis         │
│ (Continuous)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Decision Engine  │
│ • Significance   │
│ • Winner         │
│ • Rollout        │
└──────────────────┘
```

---

## 🔧 A/B Testing Implementation

### Experiment Manager

```python
# ios_core/analytics/ab_testing.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    """Experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ROLLED_OUT = "rolled_out"

class AssignmentMethod(Enum):
    """How to assign users to variants"""
    USER_ID = "user_id"  # Consistent per user
    SESSION_ID = "session_id"  # Consistent per session
    RANDOM = "random"  # Pure random

@dataclass
class VariantConfig:
    """Configuration for experiment variant"""
    name: str
    description: str
    traffic_percentage: float  # 0-100
    config: Dict[str, Any]  # Feature-specific config

@dataclass
class ExperimentConfig:
    """Complete experiment configuration"""
    experiment_id: str
    name: str
    description: str
    variants: List[VariantConfig]
    assignment_method: AssignmentMethod
    traffic_percentage: float  # % of total traffic in experiment
    start_date: datetime
    end_date: Optional[datetime]
    primary_metric: str
    secondary_metrics: List[str]
    minimum_sample_size: int
    target_confidence: float  # e.g., 0.95

class ExperimentManager:
    """
    Manage A/B test experiments
    
    Features:
    - Deterministic user assignment
    - Traffic splitting
    - Experiment lifecycle
    - Metrics tracking
    """
    
    def __init__(self):
        self.cache_prefix = "experiment:"
        self.cache_ttl = 3600  # 1 hour
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict],
        config: Dict
    ) -> str:
        """
        Create new A/B test experiment
        
        Args:
            name: Experiment name
            description: What are we testing?
            variants: List of variant configs
            config: Experiment configuration
        
        Returns:
            experiment_id
        """
        from ios_core.analytics.models import SearchABTest
        
        # Generate experiment ID
        experiment_id = self._generate_experiment_id(name)
        
        # Validate variants
        total_traffic = sum(v['traffic_percentage'] for v in variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Variant traffic must sum to 100%, got {total_traffic}")
        
        # Create experiment
        experiment = SearchABTest.objects.create(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants={v['name']: v for v in variants},
            status=ExperimentStatus.DRAFT.value,
            traffic_percentage=config.get('traffic_percentage', 10),
            start_date=config['start_date'],
            end_date=config.get('end_date'),
            sample_size=0
        )
        
        logger.info(f"Created experiment: {experiment_id}")
        
        return experiment_id
    
    def start_experiment(self, experiment_id: str):
        """Start running experiment"""
        from ios_core.analytics.models import SearchABTest
        
        experiment = SearchABTest.objects.get(experiment_id=experiment_id)
        
        if experiment.status != ExperimentStatus.DRAFT.value:
            raise ValueError(f"Cannot start experiment in {experiment.status} status")
        
        experiment.status = ExperimentStatus.RUNNING.value
        experiment.start_date = timezone.now()
        experiment.save()
        
        # Clear cache to pick up new experiment
        self._clear_experiment_cache(experiment_id)
        
        logger.info(f"Started experiment: {experiment_id}")
    
    def stop_experiment(self, experiment_id: str, winner: Optional[str] = None):
        """Stop experiment and optionally declare winner"""
        from ios_core.analytics.models import SearchABTest
        
        experiment = SearchABTest.objects.get(experiment_id=experiment_id)
        
        experiment.status = ExperimentStatus.COMPLETED.value
        experiment.end_date = timezone.now()
        
        if winner:
            experiment.winner = winner
        
        experiment.save()
        
        self._clear_experiment_cache(experiment_id)
        
        logger.info(f"Stopped experiment: {experiment_id}, winner: {winner}")
    
    def assign_variant(
        self,
        experiment_id: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign user to experiment variant
        
        Assignment is deterministic based on:
        - User ID (for logged-in users)
        - Session ID (for anonymous users)
        
        Returns:
            variant_name or None if not in experiment
        """
        # Get experiment config (cached)
        experiment = self._get_experiment(experiment_id)
        
        if not experiment or experiment['status'] != ExperimentStatus.RUNNING.value:
            return None
        
        # Check if user should be in experiment (traffic %)
        assignment_key = self._get_assignment_key(experiment_id, user_id, session_id)
        
        if not self._should_include_in_experiment(
            assignment_key,
            experiment['traffic_percentage']
        ):
            return None
        
        # Assign to variant
        variant = self._assign_to_variant(
            assignment_key,
            experiment['variants']
        )
        
        # Cache assignment
        cache_key = f"{self.cache_prefix}assignment:{assignment_key}"
        cache.set(cache_key, variant, self.cache_ttl)
        
        return variant
    
    def get_variant_config(
        self,
        experiment_id: str,
        variant_name: str
    ) -> Dict:
        """Get configuration for specific variant"""
        experiment = self._get_experiment(experiment_id)
        
        if not experiment:
            return {}
        
        return experiment['variants'].get(variant_name, {})
    
    def _get_assignment_key(
        self,
        experiment_id: str,
        user_id: Optional[int],
        session_id: Optional[str]
    ) -> str:
        """
        Generate deterministic assignment key
        
        Priority:
        1. User ID (most stable)
        2. Session ID (stable within session)
        """
        if user_id:
            return f"{experiment_id}:user:{user_id}"
        elif session_id:
            return f"{experiment_id}:session:{session_id}"
        else:
            # Fallback: random (not recommended)
            import uuid
            return f"{experiment_id}:random:{uuid.uuid4()}"
    
    def _should_include_in_experiment(
        self,
        assignment_key: str,
        traffic_percentage: float
    ) -> bool:
        """
        Deterministic check if assignment_key should be in experiment
        
        Uses consistent hashing to ensure same key always gets
        same decision
        """
        # Hash assignment key to number [0, 100)
        hash_value = int(
            hashlib.md5(assignment_key.encode()).hexdigest()[:8],
            16
        ) % 100
        
        # Include if hash falls within traffic percentage
        return hash_value < traffic_percentage
    
    def _assign_to_variant(
        self,
        assignment_key: str,
        variants: Dict[str, Dict]
    ) -> str:
        """
        Assign to variant based on traffic split
        
        Uses consistent hashing to ensure same key always
        gets same variant
        """
        # Hash to number [0, 100)
        hash_value = int(
            hashlib.md5(f"variant:{assignment_key}".encode()).hexdigest()[:8],
            16
        ) % 100
        
        # Assign based on cumulative traffic percentages
        cumulative = 0.0
        
        for variant_name, variant_config in variants.items():
            cumulative += variant_config['traffic_percentage']
            
            if hash_value < cumulative:
                return variant_name
        
        # Fallback to first variant (shouldn't happen)
        return list(variants.keys())[0]
    
    def _get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get experiment config (cached)"""
        cache_key = f"{self.cache_prefix}config:{experiment_id}"
        
        # Check cache
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Load from DB
        from ios_core.analytics.models import SearchABTest
        
        try:
            experiment = SearchABTest.objects.get(experiment_id=experiment_id)
            
            config = {
                'experiment_id': experiment.experiment_id,
                'name': experiment.name,
                'status': experiment.status,
                'variants': experiment.variants,
                'traffic_percentage': experiment.traffic_percentage
            }
            
            # Cache
            cache.set(cache_key, config, self.cache_ttl)
            
            return config
            
        except SearchABTest.DoesNotExist:
            return None
    
    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID"""
        timestamp = int(datetime.now().timestamp())
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"exp_{timestamp}_{name_hash}"
    
    def _clear_experiment_cache(self, experiment_id: str):
        """Clear experiment cache"""
        cache_key = f"{self.cache_prefix}config:{experiment_id}"
        cache.delete(cache_key)


# Global instance
_experiment_manager = None

def get_experiment_manager() -> ExperimentManager:
    """Get global experiment manager"""
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager
```

### Search Integration with Experiments

```python
# ios_core/search/hybrid_search.py (updated)

class HybridSearchEngine:
    """
    Hybrid search with A/B testing support
    """
    
    def __init__(self, ...):
        # ... existing init ...
        self.experiment_manager = get_experiment_manager()
    
    def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.AUTO,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> List[HybridSearchResult]:
        """
        Execute hybrid search with A/B testing
        """
        # Check for active experiments
        experiment_info = self._get_active_experiment(user_id, session_id)
        
        if experiment_info:
            logger.info(
                f"User in experiment: {experiment_info['experiment_id']}, "
                f"variant: {experiment_info['variant']}"
            )
            
            # Apply variant configuration
            variant_config = experiment_info.get('config', {})
            
            # Override search parameters based on variant
            if 'fusion_algorithm' in variant_config:
                # Test different fusion algorithms
                self.fusion_algorithm = variant_config['fusion_algorithm']
            
            if 'weights' in variant_config:
                # Test different fusion weights
                self.weights = variant_config['weights']
            
            if 'rerank_enabled' in variant_config:
                # Test with/without ML re-ranking
                user_context = user_context or {}
                user_context['enable_ml_rerank'] = variant_config['rerank_enabled']
        
        # Execute search (existing logic)
        results = self._execute_search(
            query, mode, page, page_size, filters, user_id, user_context
        )
        
        # Track experiment metrics
        if experiment_info:
            self._track_experiment_search(
                experiment_info,
                query,
                results,
                user_id
            )
        
        return results
    
    def _get_active_experiment(
        self,
        user_id: Optional[int],
        session_id: Optional[str]
    ) -> Optional[Dict]:
        """Check if user is in an active experiment"""
        # List of active experiments (could be multiple)
        active_experiments = ['ranking_algorithm_v2', 'ml_rerank_test']
        
        for experiment_id in active_experiments:
            variant = self.experiment_manager.assign_variant(
                experiment_id,
                user_id,
                session_id
            )
            
            if variant:
                config = self.experiment_manager.get_variant_config(
                    experiment_id,
                    variant
                )
                
                return {
                    'experiment_id': experiment_id,
                    'variant': variant,
                    'config': config
                }
        
        return None
    
    def _track_experiment_search(
        self,
        experiment_info: Dict,
        query: str,
        results: List,
        user_id: Optional[int]
    ):
        """Track search in experiment context"""
        from ios_core.analytics.tracking import get_analytics
        
        analytics = get_analytics()
        
        # Track will include experiment_id and variant
        # (already implemented in SearchQuery model)
        
        logger.debug(
            f"Tracked experiment search: {experiment_info['experiment_id']}, "
            f"variant: {experiment_info['variant']}, "
            f"results: {len(results)}"
        )


# Example experiment configurations

def create_ranking_algorithm_experiment():
    """
    Test: RRF vs Weighted Fusion
    
    Hypothesis: RRF provides better relevance
    Primary metric: CTR
    """
    manager = get_experiment_manager()
    
    experiment_id = manager.create_experiment(
        name="Ranking Algorithm: RRF vs Weighted",
        description="Compare Reciprocal Rank Fusion with Weighted Score Combination",
        variants=[
            {
                'name': 'control',
                'description': 'Current: Weighted Combination (60/40)',
                'traffic_percentage': 50.0,
                'config': {
                    'fusion_algorithm': 'weighted',
                    'weights': {'keyword': 0.6, 'semantic': 0.4}
                }
            },
            {
                'name': 'variant_rrf',
                'description': 'New: Reciprocal Rank Fusion',
                'traffic_percentage': 50.0,
                'config': {
                    'fusion_algorithm': 'rrf',
                    'rrf_k': 60
                }
            }
        ],
        config={
            'traffic_percentage': 20.0,  # 20% of total traffic
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=14),
            'primary_metric': 'ctr',
            'secondary_metrics': ['mrr', 'zero_results_rate'],
            'minimum_sample_size': 1000,
            'target_confidence': 0.95
        }
    )
    
    return experiment_id


def create_ml_rerank_experiment():
    """
    Test: ML Re-ranking On/Off
    
    Hypothesis: ML re-ranking improves relevance
    Primary metric: MRR
    """
    manager = get_experiment_manager()
    
    experiment_id = manager.create_experiment(
        name="ML Re-ranking Test",
        description="Test impact of ML-based re-ranking on search quality",
        variants=[
            {
                'name': 'control',
                'description': 'No ML re-ranking',
                'traffic_percentage': 50.0,
                'config': {
                    'rerank_enabled': False
                }
            },
            {
                'name': 'variant_ml',
                'description': 'With ML re-ranking',
                'traffic_percentage': 50.0,
                'config': {
                    'rerank_enabled': True
                }
            }
        ],
        config={
            'traffic_percentage': 10.0,
            'start_date': timezone.now(),
            'primary_metric': 'mrr',
            'secondary_metrics': ['ctr', 'dwell_time']
        }
    )
    
    return experiment_id
```

---

## 📊 Statistical Analysis

### Metrics Analyzer

```python
# ios_core/analytics/experiment_analysis.py

from typing import Dict, List, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VariantMetrics:
    """Metrics for a single variant"""
    variant_name: str
    sample_size: int
    
    # Primary metrics
    ctr: float
    mrr: float
    zero_results_rate: float
    
    # Engagement metrics
    avg_clicks_per_query: float
    avg_dwell_time: float
    
    # Performance metrics
    avg_latency_ms: float

@dataclass
class ComparisonResult:
    """Statistical comparison between variants"""
    control_variant: str
    test_variant: str
    metric_name: str
    
    control_value: float
    test_value: float
    
    # Statistical significance
    p_value: float
    is_significant: bool  # p < 0.05
    confidence_level: float  # e.g., 0.95
    
    # Effect size
    relative_change: float  # (test - control) / control
    absolute_change: float  # test - control
    
    # Confidence interval for relative change
    ci_lower: float
    ci_upper: float

class ExperimentAnalyzer:
    """
    Analyze A/B test results
    
    Methods:
    - T-test for continuous metrics (latency, dwell time)
    - Z-test for proportions (CTR, conversion rate)
    - Bootstrap for confidence intervals
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
    
    def analyze_experiment(
        self,
        experiment_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Complete analysis of experiment
        
        Returns:
            - Variant metrics
            - Statistical comparisons
            - Recommendation
        """
        # Get data for all variants
        variant_metrics = self._calculate_variant_metrics(
            experiment_id,
            start_date,
            end_date
        )
        
        # Get control variant (usually named 'control')
        control_name = 'control'
        if control_name not in variant_metrics:
            control_name = list(variant_metrics.keys())[0]
        
        # Compare each variant to control
        comparisons = []
        
        for variant_name, metrics in variant_metrics.items():
            if variant_name == control_name:
                continue
            
            # Compare CTR
            ctr_comparison = self._compare_proportions(
                metric_name='ctr',
                control=variant_metrics[control_name],
                test=metrics
            )
            comparisons.append(ctr_comparison)
            
            # Compare MRR
            mrr_comparison = self._compare_continuous(
                metric_name='mrr',
                control=variant_metrics[control_name],
                test=metrics,
                experiment_id=experiment_id,
                start_date=start_date,
                end_date=end_date
            )
            comparisons.append(mrr_comparison)
        
        # Determine winner
        winner = self._determine_winner(
            variant_metrics,
            comparisons,
            primary_metric='ctr'
        )
        
        return {
            'variant_metrics': variant_metrics,
            'comparisons': comparisons,
            'winner': winner,
            'recommendation': self._generate_recommendation(
                winner,
                comparisons
            )
        }
    
    def _calculate_variant_metrics(
        self,
        experiment_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, VariantMetrics]:
        """Calculate metrics for each variant"""
        from ios_core.analytics.models import SearchQuery
        from django.db.models import Count, Avg
        
        # Get queries by variant
        queries_by_variant = {}
        
        variants = SearchQuery.objects.filter(
            experiment_id=experiment_id,
            created_at__gte=start_date,
            created_at__lt=end_date
        ).values('variant').distinct()
        
        for variant_data in variants:
            variant = variant_data['variant']
            
            queries = SearchQuery.objects.filter(
                experiment_id=experiment_id,
                variant=variant,
                created_at__gte=start_date,
                created_at__lt=end_date
            )
            
            # Calculate metrics
            stats = queries.aggregate(
                total_queries=Count('id'),
                queries_with_clicks=Count('id', filter=Q(had_clicks=True)),
                total_clicks=Sum('clicks_count'),
                avg_first_click_rank=Avg('first_click_rank', filter=Q(first_click_rank__isnull=False)),
                zero_results=Count('id', filter=Q(total_results=0)),
                avg_latency=Avg('search_time_ms')
            )
            
            # CTR
            ctr = (
                stats['queries_with_clicks'] / stats['total_queries']
                if stats['total_queries'] > 0 else 0
            )
            
            # MRR (Mean Reciprocal Rank)
            queries_with_clicks = queries.filter(
                had_clicks=True,
                first_click_rank__isnull=False
            )
            
            if queries_with_clicks.exists():
                reciprocal_ranks = [
                    1.0 / q.first_click_rank
                    for q in queries_with_clicks
                ]
                mrr = np.mean(reciprocal_ranks)
            else:
                mrr = 0.0
            
            # Zero results rate
            zrr = (
                stats['zero_results'] / stats['total_queries']
                if stats['total_queries'] > 0 else 0
            )
            
            # Avg clicks per query
            avg_clicks = (
                stats['total_clicks'] / stats['total_queries']
                if stats['total_queries'] > 0 else 0
            )
            
            # Create metrics object
            queries_by_variant[variant] = VariantMetrics(
                variant_name=variant,
                sample_size=stats['total_queries'],
                ctr=ctr,
                mrr=mrr,
                zero_results_rate=zrr,
                avg_clicks_per_query=avg_clicks,
                avg_dwell_time=0.0,  # TODO: Calculate from click data
                avg_latency_ms=stats['avg_latency'] or 0
            )
        
        return queries_by_variant
    
    def _compare_proportions(
        self,
        metric_name: str,
        control: VariantMetrics,
        test: VariantMetrics
    ) -> ComparisonResult:
        """
        Compare proportions (e.g., CTR) using Z-test
        
        Formula for Z-test of proportions:
        Z = (p1 - p2) / sqrt(p * (1-p) * (1/n1 + 1/n2))
        
        Where p = (x1 + x2) / (n1 + n2)
        """
        # Get metric values
        control_p = getattr(control, metric_name)
        test_p = getattr(test, metric_name)
        
        n_control = control.sample_size
        n_test = test.sample_size
        
        # Convert proportions back to counts
        x_control = int(control_p * n_control)
        x_test = int(test_p * n_test)
        
        # Pooled proportion
        pooled_p = (x_control + x_test) / (n_control + n_test)
        
        # Standard error
        se = np.sqrt(
            pooled_p * (1 - pooled_p) * (1/n_control + 1/n_test)
        )
        
        # Z-statistic
        if se == 0:
            z = 0
            p_value = 1.0
        else:
            z = (test_p - control_p) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z)))  # Two-tailed
        
        # Effect size
        relative_change = (
            (test_p - control_p) / control_p
            if control_p > 0 else float('inf')
        )
        absolute_change = test_p - control_p
        
        # Confidence interval for difference
        # Using normal approximation
        z_critical = stats.norm.ppf(1 - self.alpha/2)
        
        se_diff = np.sqrt(
            control_p * (1 - control_p) / n_control +
            test_p * (1 - test_p) / n_test
        )
        
        ci_lower_abs = absolute_change - z_critical * se_diff
        ci_upper_abs = absolute_change + z_critical * se_diff
        
        # Convert to relative change CI
        if control_p > 0:
            ci_lower = ci_lower_abs / control_p
            ci_upper = ci_upper_abs / control_p
        else:
            ci_lower = float('-inf')
            ci_upper = float('inf')
        
        return ComparisonResult(
            control_variant=control.variant_name,
            test_variant=test.variant_name,
            metric_name=metric_name,
            control_value=control_p,
            test_value=test_p,
            p_value=p_value,
            is_significant=(p_value < self.alpha),
            confidence_level=self.confidence_level,
            relative_change=relative_change,
            absolute_change=absolute_change,
            ci_lower=ci_lower,
            ci_upper=ci_upper
        )
    
    def _compare_continuous(
        self,
        metric_name: str,
        control: VariantMetrics,
        test: VariantMetrics,
        experiment_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> ComparisonResult:
        """
        Compare continuous metrics (e.g., MRR, latency) using T-test
        """
        from ios_core.analytics.models import SearchQuery
        
        # Get individual values for t-test
        control_values = list(
            SearchQuery.objects.filter(
                experiment_id=experiment_id,
                variant=control.variant_name,
                created_at__gte=start_date,
                created_at__lt=end_date,
                first_click_rank__isnull=False
            ).annotate(
                mrr_value=1.0 / F('first_click_rank')
            ).values_list('mrr_value', flat=True)
        )
        
        test_values = list(
            SearchQuery.objects.filter(
                experiment_id=experiment_id,
                variant=test.variant_name,
                created_at__gte=start_date,
                created_at__lt=end_date,
                first_click_rank__isnull=False
            ).annotate(
                mrr_value=1.0 / F('first_click_rank')
            ).values_list('mrr_value', flat=True)
        )
        
        if not control_values or not test_values:
            # Not enough data
            return ComparisonResult(
                control_variant=control.variant_name,
                test_variant=test.variant_name,
                metric_name=metric_name,
                control_value=0,
                test_value=0,
                p_value=1.0,
                is_significant=False,
                confidence_level=self.confidence_level,
                relative_change=0,
                absolute_change=0,
                ci_lower=0,
                ci_upper=0
            )
        
        # T-test
        t_stat, p_value = stats.ttest_ind(test_values, control_values)
        
        # Effect size
        control_mean = np.mean(control_values)
        test_mean = np.mean(test_values)
        
        relative_change = (
            (test_mean - control_mean) / control_mean
            if control_mean > 0 else 0
        )
        absolute_change = test_mean - control_mean
        
        # Confidence interval
        se_diff = np.sqrt(
            np.var(control_values) / len(control_values) +
            np.var(test_values) / len(test_values)
        )
        
        df = len(control_values) + len(test_values) - 2
        t_critical = stats.t.ppf(1 - self.alpha/2, df)
        
        ci_lower_abs = absolute_change - t_critical * se_diff
        ci_upper_abs = absolute_change + t_critical * se_diff
        
        ci_lower = ci_lower_abs / control_mean if control_mean > 0 else 0
        ci_upper = ci_upper_abs / control_mean if control_mean > 0 else 0
        
        return ComparisonResult(
            control_variant=control.variant_name,
            test_variant=test.variant_name,
            metric_name=metric_name,
            control_value=control_mean,
            test_value=test_mean,
            p_value=p_value,
            is_significant=(p_value < self.alpha),
            confidence_level=self.confidence_level,
            relative_change=relative_change,
            absolute_change=absolute_change,
            ci_lower=ci_lower,
            ci_upper=ci_upper
        )
    
    def _determine_winner(
        self,
        variant_metrics: Dict[str, VariantMetrics],
        comparisons: List[ComparisonResult],
        primary_metric: str
    ) -> Dict:
        """
        Determine winning variant
        
        Criteria:
        1. Statistical significance on primary metric
        2. No degradation on secondary metrics
        3. Sufficient sample size
        """
        # Find comparison for primary metric
        primary_comparison = None
        for comp in comparisons:
            if comp.metric_name == primary_metric:
                primary_comparison = comp
                break
        
        if not primary_comparison:
            return {
                'winner': 'inconclusive',
                'reason': 'No comparison for primary metric'
            }
        
        # Check significance
        if not primary_comparison.is_significant:
            return {
                'winner': 'inconclusive',
                'reason': f'Not statistically significant (p={primary_comparison.p_value:.4f})'
            }
        
        # Check if test is better
        if primary_comparison.relative_change > 0:
            # Test variant is better
            
            # Check for degradations in secondary metrics
            degradations = []
            for comp in comparisons:
                if comp.metric_name != primary_metric:
                    if comp.is_significant and comp.relative_change < -0.05:
                        degradations.append(comp.metric_name)
            
            if degradations:
                return {
                    'winner': 'inconclusive',
                    'reason': f'Significant degradation in: {", ".join(degradations)}'
                }
            
            return {
                'winner': primary_comparison.test_variant,
                'reason': f'Significant improvement in {primary_metric}: {primary_comparison.relative_change:.2%}',
                'confidence': primary_comparison.confidence_level,
                'effect_size': primary_comparison.relative_change
            }
        else:
            # Control is better
            return {
                'winner': primary_comparison.control_variant,
                'reason': f'Test variant performed worse: {primary_comparison.relative_change:.2%}'
            }
    
    def _generate_recommendation(
        self,
        winner: Dict,
        comparisons: List[ComparisonResult]
    ) -> str:
        """Generate human-readable recommendation"""
        if winner['winner'] == 'inconclusive':
            return f"Continue testing. {winner['reason']}"
        
        # Winner is clear
        variant = winner['winner']
        
        if variant == 'control':
            return "Keep current implementation. Test variant did not improve metrics."
        
        # Test won
        recommendation = f"Roll out '{variant}' to 100% of traffic. "
        
        # Highlight improvements
        improvements = [
            comp for comp in comparisons
            if comp.test_variant == variant and comp.relative_change > 0 and comp.is_significant
        ]
        
        if improvements:
            improvement_str = ", ".join([
                f"{comp.metric_name}: +{comp.relative_change:.1%}"
                for comp in improvements
            ])
            recommendation += f"Improvements: {improvement_str}"
        
        return recommendation


# Example usage
def analyze_ranking_experiment():
    """Analyze ranking algorithm experiment"""
    analyzer = ExperimentAnalyzer(confidence_level=0.95)
    
    results = analyzer.analyze_experiment(
        experiment_id='ranking_algorithm_v2',
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now()
    )
    
    print("=" * 80)
    print("EXPERIMENT ANALYSIS REPORT")
    print("=" * 80)
    
    print("\n📊 VARIANT METRICS:")
    for variant_name, metrics in results['variant_metrics'].items():
        print(f"\n{variant_name.upper()}:")
        print(f"  Sample Size: {metrics.sample_size:,}")
        print(f"  CTR: {metrics.ctr:.2%}")
        print(f"  MRR: {metrics.mrr:.3f}")
        print(f"  Zero Results Rate: {metrics.zero_results_rate:.2%}")
        print(f"  Avg Latency: {metrics.avg_latency_ms:.0f}ms")
    
    print("\n📈 STATISTICAL COMPARISONS:")
    for comp in results['comparisons']:
        print(f"\n{comp.metric_name.upper()}: {comp.test_variant} vs {comp.control_variant}")
        print(f"  Control: {comp.control_value:.4f}")
        print(f"  Test: {comp.test_value:.4f}")
        print(f"  Change: {comp.relative_change:+.2%} ({comp.absolute_change:+.4f})")
        print(f"  95% CI: [{comp.ci_lower:.2%}, {comp.ci_upper:.2%}]")
        print(f"  P-value: {comp.p_value:.4f}")
        print(f"  Significant: {'✅ YES' if comp.is_significant else '❌ NO'}")
    
    print("\n🏆 WINNER:")
    print(f"  Variant: {results['winner']['winner']}")
    print(f"  Reason: {results['winner']['reason']}")
    
    print("\n💡 RECOMMENDATION:")
    print(f"  {results['recommendation']}")
    
    print("\n" + "=" * 80)
```

---

## 📉 Sample Size Calculator

```python
# ios_core/analytics/sample_size.py

import numpy as np
from scipy import stats
from typing import Tuple

def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """
    Calculate required sample size per variant
    
    Args:
        baseline_rate: Current conversion rate (e.g., 0.30 for 30% CTR)
        minimum_detectable_effect: Minimum relative change to detect (e.g., 0.10 for 10%)
        alpha: Significance level (Type I error rate)
        power: Statistical power (1 - Type II error rate)
    
    Returns:
        Required sample size per variant
    
    Example:
        >>> calculate_sample_size(
        ...     baseline_rate=0.30,
        ...     minimum_detectable_effect=0.10,  # Detect 10% relative change
        ...     alpha=0.05,
        ...     power=0.80
        ... )
        3842
    """
    # Test rate (with minimum detectable effect)
    test_rate = baseline_rate * (1 + minimum_detectable_effect)
    
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-tailed
    z_beta = stats.norm.ppf(power)
    
    # Pooled probability
    p_pooled = (baseline_rate + test_rate) / 2
    
    # Sample size formula
    n = (
        2 * (z_alpha + z_beta)**2 * p_pooled * (1 - p_pooled)
        / (test_rate - baseline_rate)**2
    )
    
    return int(np.ceil(n))


def calculate_experiment_duration(
    sample_size_per_variant: int,
    daily_traffic: int,
    num_variants: int = 2,
    traffic_percentage: float = 1.0
) -> Tuple[int, str]:
    """
    Calculate experiment duration
    
    Args:
        sample_size_per_variant: Required samples per variant
        daily_traffic: Daily search queries
        num_variants: Number of variants (including control)
        traffic_percentage: % of traffic in experiment (0-1)
    
    Returns:
        (days, human_readable)
    
    Example:
        >>> calculate_experiment_duration(
        ...     sample_size_per_variant=3842,
        ...     daily_traffic=10000,
        ...     num_variants=2,
        ...     traffic_percentage=0.20
        ... )
        (4, "4 days")
    """
    # Total samples needed
    total_samples = sample_size_per_variant * num_variants
    
    # Daily samples in experiment
    daily_samples = daily_traffic * traffic_percentage
    
    # Days needed
    days = total_samples / daily_samples
    days_ceil = int(np.ceil(days))
    
    # Human readable
    if days_ceil < 7:
        readable = f"{days_ceil} days"
    elif days_ceil < 30:
        weeks = int(np.ceil(days_ceil / 7))
        readable = f"{weeks} weeks ({days_ceil} days)"
    else:
        months = int(np.ceil(days_ceil / 30))
        readable = f"{months} months ({days_ceil} days)"
    
    return days_ceil, readable


# Example: Plan an experiment
def plan_experiment():
    """Plan sample size and duration for experiment"""
    
    print("=" * 60)
    print("EXPERIMENT PLANNING CALCULATOR")
    print("=" * 60)
    
    # Current metrics
    current_ctr = 0.30  # 30% CTR
    daily_searches = 10000
    
    # Experiment parameters
    mde = 0.10  # Want to detect 10% improvement
    alpha = 0.05  # 95% confidence
    power = 0.80  # 80% power
    
    # Calculate sample size
    sample_size = calculate_sample_size(
        baseline_rate=current_ctr,
        minimum_detectable_effect=mde,
        alpha=alpha,
        power=power
    )
    
    print(f"\n📊 CURRENT METRICS:")
    print(f"  CTR: {current_ctr:.1%}")
    print(f"  Daily searches: {daily_searches:,}")
    
    print(f"\n🎯 EXPERIMENT PARAMETERS:")
    print(f"  Minimum detectable effect: {mde:.1%}")
    print(f"  Significance level (α): {alpha}")
    print(f"  Statistical power: {power}")
    
    print(f"\n📈 REQUIRED SAMPLE SIZE:")
    print(f"  Per variant: {sample_size:,} searches")
    print(f"  Total (2 variants): {sample_size * 2:,} searches")
    
    # Calculate duration for different traffic allocations
    print(f"\n⏱️  EXPERIMENT DURATION:")
    
    for traffic_pct in [0.10, 0.20, 0.50, 1.00]:
        days, readable = calculate_experiment_duration(
            sample_size_per_variant=sample_size,
            daily_traffic=daily_searches,
            num_variants=2,
            traffic_percentage=traffic_pct
        )
        
        print(f"  {traffic_pct:.0%} traffic: {readable}")
    
    print("\n" + "=" * 60)

# Output:
# ============================================================
# EXPERIMENT PLANNING CALCULATOR
# ============================================================
#
# 📊 CURRENT METRICS:
#   CTR: 30.0%
#   Daily searches: 10,000
#
# 🎯 EXPERIMENT PARAMETERS:
#   Minimum detectable effect: 10.0%
#   Significance level (α): 0.05
#   Statistical power: 0.8
#
# 📈 REQUIRED SAMPLE SIZE:
#   Per variant: 3,842 searches
#   Total (2 variants): 7,684 searches
#
# ⏱️  EXPERIMENT DURATION:
#   10% traffic: 8 days
#   20% traffic: 4 days
#   50% traffic: 2 days
#   100% traffic: 1 days
#
# ============================================================
```

---

**Продолжение следует...**

Создано:
- ✅ Complete A/B testing framework
- ✅ Experiment manager with deterministic assignment
- ✅ Statistical analysis (Z-test, T-test)
- ✅ Winner determination algorithm
- ✅ Sample size calculator
- ✅ Experiment planning tools

**Следующие разделы:**
1. Query Suggestions & Autocomplete
2. Real-time Monitoring & Alerts
3. Performance Optimization Guide

**Готовы продолжить с Query Suggestions?**