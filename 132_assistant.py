Отлично! Пользователь готов продолжить с Query Suggestions & Autocomplete. Это следующая важная часть поисковой системы. Мне нужно создать подробное руководство по:

1. Autocomplete/Query Suggestions Architecture
2. Trie-based suggestion engine
3. Popular query tracking
4. Typo correction / spell checking
5. Query expansion
6. Personalized suggestions
7. Performance optimization

Продолжу в том же стиле - подробный technical deep-dive с кодом и примерами.# 🎯 DEEP-DIVE: SEARCH SYSTEM (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 7: `docs/deep-dive/search/QUERY_SUGGESTIONS.md`

```markdown
# Query Suggestions & Autocomplete - Deep Dive

## 🔍 Suggestion System Architecture

### Overall Flow

```
User Types: "perso"
       │
       ▼
┌──────────────────────────┐
│ Autocomplete Request     │
│ • Prefix: "perso"        │
│ • User context           │
└────────────┬─────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐     ┌──────────┐
│ Trie    │     │ Popular  │
│ Search  │     │ Queries  │
└────┬────┘     └─────┬────┘
     │                │
     │   Results (10) │ Results (10)
     │                │
     └────────┬───────┘
              │
              ▼
    ┌──────────────────┐
    │ Result Merger    │
    │ • Dedup          │
    │ • Ranking        │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Personalization  │
    │ • User history   │
    │ • Boost relevant │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Spell Check      │
    │ • Typo detection │
    │ • Corrections    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Final Results    │
    │ [                │
    │   "personal budget",│
    │   "persönliches budget",│
    │   "person assistance"│
    │ ]                │
    └──────────────────┘
```

---

## 🌲 Trie-Based Autocomplete

### Trie Data Structure

```python
# ios_core/search/autocomplete/trie.py

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import redis
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class SuggestionCandidate:
    """Single autocomplete suggestion"""
    text: str
    score: float  # Popularity/relevance score
    metadata: Dict  # Additional info (frequency, last_used, etc.)

class TrieNode:
    """
    Node in Trie data structure
    
    Stores:
    - Children nodes (dict)
    - Is end of word (bool)
    - Suggestions at this node (list)
    """
    
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end_of_word: bool = False
        self.suggestions: List[SuggestionCandidate] = []
        self.max_suggestions: int = 10
    
    def add_suggestion(self, candidate: SuggestionCandidate):
        """Add suggestion and maintain top-K by score"""
        self.suggestions.append(candidate)
        
        # Keep only top-K suggestions
        self.suggestions.sort(key=lambda x: x.score, reverse=True)
        self.suggestions = self.suggestions[:self.max_suggestions]

class AutocompleteTrie:
    """
    Trie for fast prefix-based autocomplete
    
    Features:
    - O(k) prefix search where k = prefix length
    - Pre-computed suggestions at each node
    - Support for multiple languages
    - Fuzzy matching (optional)
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.root = TrieNode()
        self.redis = redis_client
        self.cache_prefix = "autocomplete:trie:"
    
    def insert(self, text: str, score: float = 1.0, metadata: Optional[Dict] = None):
        """
        Insert text into trie
        
        Args:
            text: Query text to insert
            score: Importance/popularity score
            metadata: Additional metadata
        """
        text = text.lower().strip()
        
        if not text:
            return
        
        node = self.root
        
        # Insert each character
        for char in text:
            if char not in node.children:
                node.children[char] = TrieNode()
            
            node = node.children[char]
            
            # Add suggestion at this prefix level
            candidate = SuggestionCandidate(
                text=text,
                score=score,
                metadata=metadata or {}
            )
            node.add_suggestion(candidate)
        
        # Mark end of word
        node.is_end_of_word = True
    
    def search(
        self,
        prefix: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[SuggestionCandidate]:
        """
        Search for autocomplete suggestions
        
        Args:
            prefix: Query prefix
            limit: Max suggestions to return
            min_score: Minimum score threshold
        
        Returns:
            List of suggestions sorted by score
        """
        prefix = prefix.lower().strip()
        
        if not prefix:
            return []
        
        # Navigate to prefix node
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                # Prefix not found
                return []
            node = node.children[char]
        
        # Get pre-computed suggestions at this node
        suggestions = [
            s for s in node.suggestions
            if s.score >= min_score
        ][:limit]
        
        return suggestions
    
    def bulk_insert(self, queries: List[Dict]):
        """
        Bulk insert queries
        
        Args:
            queries: List of {text, score, metadata}
        """
        for query in queries:
            self.insert(
                text=query['text'],
                score=query.get('score', 1.0),
                metadata=query.get('metadata')
            )
    
    def save_to_redis(self):
        """Serialize trie to Redis"""
        if not self.redis:
            logger.warning("Redis client not configured")
            return
        
        # Serialize trie structure
        serialized = self._serialize_node(self.root)
        
        # Save to Redis
        key = f"{self.cache_prefix}root"
        self.redis.set(key, json.dumps(serialized))
        
        logger.info("Saved trie to Redis")
    
    def load_from_redis(self):
        """Load trie from Redis"""
        if not self.redis:
            logger.warning("Redis client not configured")
            return
        
        key = f"{self.cache_prefix}root"
        serialized = self.redis.get(key)
        
        if serialized:
            data = json.loads(serialized)
            self.root = self._deserialize_node(data)
            logger.info("Loaded trie from Redis")
        else:
            logger.warning("No trie data found in Redis")
    
    def _serialize_node(self, node: TrieNode) -> Dict:
        """Recursively serialize trie node"""
        return {
            'is_end': node.is_end_of_word,
            'suggestions': [
                {
                    'text': s.text,
                    'score': s.score,
                    'metadata': s.metadata
                }
                for s in node.suggestions
            ],
            'children': {
                char: self._serialize_node(child)
                for char, child in node.children.items()
            }
        }
    
    def _deserialize_node(self, data: Dict) -> TrieNode:
        """Recursively deserialize trie node"""
        node = TrieNode()
        node.is_end_of_word = data['is_end']
        
        # Restore suggestions
        node.suggestions = [
            SuggestionCandidate(
                text=s['text'],
                score=s['score'],
                metadata=s['metadata']
            )
            for s in data['suggestions']
        ]
        
        # Restore children
        node.children = {
            char: self._deserialize_node(child_data)
            for char, child_data in data['children'].items()
        }
        
        return node
    
    def get_all_completions(self, prefix: str) -> List[str]:
        """
        Get all possible completions for prefix
        (Used for testing/debugging)
        """
        prefix = prefix.lower().strip()
        
        # Navigate to prefix
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all completions
        completions = []
        self._collect_words(node, prefix, completions)
        
        return completions
    
    def _collect_words(self, node: TrieNode, prefix: str, results: List[str]):
        """Recursively collect all words from node"""
        if node.is_end_of_word:
            results.append(prefix)
        
        for char, child in node.children.items():
            self._collect_words(child, prefix + char, results)


# Example usage
def build_autocomplete_index():
    """Build autocomplete index from query log"""
    from ios_core.analytics.models import SearchQuery
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Get popular queries from last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    popular_queries = SearchQuery.objects.filter(
        created_at__gte=thirty_days_ago
    ).values('normalized_query').annotate(
        frequency=Count('id')
    ).filter(
        frequency__gte=5  # Minimum 5 occurrences
    ).order_by('-frequency')[:10000]
    
    # Build trie
    trie = AutocompleteTrie()
    
    for query in popular_queries:
        text = query['normalized_query']
        frequency = query['frequency']
        
        # Score = log(frequency) for better distribution
        import math
        score = math.log1p(frequency)
        
        trie.insert(
            text=text,
            score=score,
            metadata={'frequency': frequency}
        )
    
    print(f"Built trie with {len(popular_queries)} queries")
    
    # Test
    suggestions = trie.search("perso", limit=5)
    print("\nSuggestions for 'perso':")
    for s in suggestions:
        print(f"  {s.text} (score: {s.score:.2f})")
    
    return trie
```

---

## 📊 Popular Query Tracking

### Query Popularity Service

```python
# ios_core/search/autocomplete/popularity.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Count, Q
import redis
import logging

logger = logging.getLogger(__name__)

class QueryPopularityTracker:
    """
    Track and rank queries by popularity
    
    Features:
    - Real-time popularity updates
    - Time-decay (recent queries ranked higher)
    - Trending queries detection
    - Personalized popularity (per user segment)
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.cache_prefix = "query:popular:"
        self.trending_prefix = "query:trending:"
    
    def track_query(
        self,
        query: str,
        user_id: Optional[int] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Track query occurrence
        
        Updates:
        - Global popularity
        - User segment popularity
        - Time-based popularity
        """
        if not self.redis:
            return
        
        query = query.lower().strip()
        timestamp = timestamp or datetime.now()
        
        # Update global popularity (sorted set)
        # Score = count (incremented)
        self.redis.zincrby(
            f"{self.cache_prefix}global",
            1,
            query
        )
        
        # Update hourly popularity (for trending)
        hour_key = timestamp.strftime("%Y%m%d%H")
        self.redis.zincrby(
            f"{self.trending_prefix}{hour_key}",
            1,
            query
        )
        
        # Expire hourly key after 7 days
        self.redis.expire(
            f"{self.trending_prefix}{hour_key}",
            7 * 24 * 3600
        )
        
        # Update user segment popularity (if user_id provided)
        if user_id:
            # Simplified: segment by user_id % 10
            segment = user_id % 10
            self.redis.zincrby(
                f"{self.cache_prefix}segment:{segment}",
                1,
                query
            )
    
    def get_popular_queries(
        self,
        limit: int = 100,
        user_segment: Optional[int] = None
    ) -> List[Dict]:
        """
        Get most popular queries
        
        Args:
            limit: Max queries to return
            user_segment: Optional user segment for personalization
        
        Returns:
            List of {query, score}
        """
        if not self.redis:
            return []
        
        # Choose key based on segmentation
        if user_segment is not None:
            key = f"{self.cache_prefix}segment:{user_segment}"
        else:
            key = f"{self.cache_prefix}global"
        
        # Get top queries with scores
        results = self.redis.zrevrange(
            key,
            0,
            limit - 1,
            withscores=True
        )
        
        return [
            {
                'query': query.decode('utf-8') if isinstance(query, bytes) else query,
                'score': float(score)
            }
            for query, score in results
        ]
    
    def get_trending_queries(
        self,
        hours: int = 24,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get trending queries (sudden popularity increase)
        
        Algorithm:
        1. Get queries from last N hours
        2. Get queries from previous N hours
        3. Calculate growth rate
        4. Rank by growth rate
        """
        if not self.redis:
            return []
        
        now = datetime.now()
        
        # Current period queries
        current_queries = {}
        for i in range(hours):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y%m%d%H")
            
            results = self.redis.zrange(
                f"{self.trending_prefix}{hour_key}",
                0,
                -1,
                withscores=True
            )
            
            for query, score in results:
                query_str = query.decode('utf-8') if isinstance(query, bytes) else query
                current_queries[query_str] = current_queries.get(query_str, 0) + score
        
        # Previous period queries
        previous_queries = {}
        for i in range(hours, hours * 2):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime("%Y%m%d%H")
            
            results = self.redis.zrange(
                f"{self.trending_prefix}{hour_key}",
                0,
                -1,
                withscores=True
            )
            
            for query, score in results:
                query_str = query.decode('utf-8') if isinstance(query, bytes) else query
                previous_queries[query_str] = previous_queries.get(query_str, 0) + score
        
        # Calculate growth rates
        trending = []
        for query, current_count in current_queries.items():
            previous_count = previous_queries.get(query, 0)
            
            # Avoid division by zero
            if previous_count == 0:
                growth_rate = float('inf') if current_count > 0 else 0
            else:
                growth_rate = (current_count - previous_count) / previous_count
            
            # Only include if significant increase and minimum volume
            if growth_rate > 0.5 and current_count > 10:
                trending.append({
                    'query': query,
                    'current_count': current_count,
                    'previous_count': previous_count,
                    'growth_rate': growth_rate,
                    'score': current_count * (1 + growth_rate)  # Combined score
                })
        
        # Sort by combined score
        trending.sort(key=lambda x: x['score'], reverse=True)
        
        return trending[:limit]
    
    def rebuild_from_analytics(self):
        """
        Rebuild popularity index from analytics database
        (Run periodically, e.g., daily)
        """
        from ios_core.analytics.models import SearchQuery
        from django.utils import timezone
        
        if not self.redis:
            logger.warning("Redis not configured")
            return
        
        # Get queries from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        popular = SearchQuery.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('normalized_query').annotate(
            count=Count('id')
        ).filter(
            count__gte=5
        ).order_by('-count')[:10000]
        
        # Clear existing data
        self.redis.delete(f"{self.cache_prefix}global")
        
        # Rebuild
        for query_data in popular:
            query = query_data['normalized_query']
            count = query_data['count']
            
            self.redis.zadd(
                f"{self.cache_prefix}global",
                {query: count}
            )
        
        logger.info(f"Rebuilt popularity index with {len(popular)} queries")


# Example usage
def track_and_suggest():
    """Example: Track queries and provide suggestions"""
    import redis
    
    # Initialize
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    tracker = QueryPopularityTracker(redis_client)
    
    # Track some queries
    queries = [
        "personal budget",
        "personal budget application",
        "persönliches budget",
        "budget hilfe",
        "budget beantragen"
    ]
    
    for query in queries:
        for _ in range(10):  # Simulate multiple searches
            tracker.track_query(query)
    
    # Get popular queries
    popular = tracker.get_popular_queries(limit=10)
    
    print("Popular Queries:")
    for item in popular:
        print(f"  {item['query']} (score: {item['score']})")
```

---

## 🔤 Spell Checking & Typo Correction

### Fuzzy Matching Engine

```python
# ios_core/search/autocomplete/spell_check.py

from typing import List, Dict, Optional, Tuple
import re
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SpellChecker:
    """
    Spell checker for query correction
    
    Features:
    - Edit distance calculation (Levenshtein)
    - Phonetic matching (Soundex/Metaphone)
    - Context-aware corrections
    - Language-specific rules
    """
    
    def __init__(self):
        self.dictionary: Set[str] = set()
        self.word_frequencies: Dict[str, int] = {}
        self.max_edit_distance = 2
    
    def build_dictionary(self, queries: List[str]):
        """Build dictionary from query log"""
        for query in queries:
            words = query.lower().split()
            for word in words:
                self.dictionary.add(word)
                self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
    
    def check_spelling(self, text: str) -> List[Dict]:
        """
        Check spelling and suggest corrections
        
        Returns:
            List of {word, is_correct, suggestions}
        """
        words = text.lower().split()
        results = []
        
        for word in words:
            if word in self.dictionary:
                results.append({
                    'word': word,
                    'is_correct': True,
                    'suggestions': []
                })
            else:
                # Find corrections
                suggestions = self.get_corrections(word, max_suggestions=5)
                
                results.append({
                    'word': word,
                    'is_correct': False,
                    'suggestions': suggestions
                })
        
        return results
    
    def get_corrections(
        self,
        word: str,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """
        Get spelling corrections for word
        
        Returns:
            List of {suggestion, distance, frequency}
        """
        candidates = []
        
        # Generate candidates within edit distance
        for dict_word in self.dictionary:
            distance = self.levenshtein_distance(word, dict_word)
            
            if distance <= self.max_edit_distance:
                candidates.append({
                    'suggestion': dict_word,
                    'distance': distance,
                    'frequency': self.word_frequencies.get(dict_word, 0)
                })
        
        # Sort by distance (lower better), then frequency (higher better)
        candidates.sort(key=lambda x: (x['distance'], -x['frequency']))
        
        return candidates[:max_suggestions]
    
    def suggest_query_correction(self, query: str) -> Optional[str]:
        """
        Suggest corrected query
        
        Returns:
            Corrected query or None if no corrections needed
        """
        check_results = self.check_spelling(query)
        
        # Check if any corrections needed
        has_errors = any(not r['is_correct'] for r in check_results)
        
        if not has_errors:
            return None
        
        # Build corrected query
        corrected_words = []
        
        for result in check_results:
            if result['is_correct']:
                corrected_words.append(result['word'])
            else:
                # Use best suggestion
                if result['suggestions']:
                    best = result['suggestions'][0]
                    corrected_words.append(best['suggestion'])
                else:
                    # No suggestion, keep original
                    corrected_words.append(result['word'])
        
        corrected_query = ' '.join(corrected_words)
        
        # Only return if different from original
        if corrected_query.lower() != query.lower():
            return corrected_query
        
        return None
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculate Levenshtein edit distance
        
        Dynamic programming approach: O(m*n) time, O(n) space
        """
        if len(s1) < len(s2):
            return SpellChecker.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        # Use only one row for space efficiency
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                # Cost of operations
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def soundex(word: str) -> str:
        """
        Soundex phonetic algorithm
        
        Encodes words by sound (English)
        """
        word = word.upper()
        
        # Keep first letter
        soundex_code = word[0]
        
        # Mapping table
        mapping = {
            'BFPV': '1',
            'CGJKQSXZ': '2',
            'DT': '3',
            'L': '4',
            'MN': '5',
            'R': '6'
        }
        
        # Encode remaining letters
        for char in word[1:]:
            for key, code in mapping.items():
                if char in key:
                    # Don't add duplicate codes
                    if code != soundex_code[-1]:
                        soundex_code += code
                    break
        
        # Pad or truncate to 4 characters
        soundex_code = soundex_code.ljust(4, '0')[:4]
        
        return soundex_code


class GermanSpellChecker(SpellChecker):
    """
    German-specific spell checker
    
    Handles:
    - Umlauts (ä, ö, ü, ß)
    - Compound words
    - Common substitutions
    """
    
    def __init__(self):
        super().__init__()
        
        # German-specific substitutions
        self.substitutions = {
            'ae': 'ä',
            'oe': 'ö',
            'ue': 'ü',
            'ss': 'ß'
        }
    
    def normalize_german(self, text: str) -> str:
        """Normalize German text"""
        text = text.lower()
        
        # Apply substitutions
        for from_str, to_str in self.substitutions.items():
            text = text.replace(from_str, to_str)
        
        return text
    
    def check_spelling(self, text: str) -> List[Dict]:
        """Check spelling with German normalization"""
        normalized = self.normalize_german(text)
        return super().check_spelling(normalized)


# Example usage
def demo_spell_checker():
    """Demo spell checking"""
    
    # Build dictionary from common queries
    queries = [
        "personal budget",
        "persönliches budget",
        "budget application",
        "budget hilfe",
        "assistance program"
    ]
    
    checker = GermanSpellChecker()
    checker.build_dictionary(queries)
    
    # Test corrections
    test_queries = [
        "personel buget",  # Typos
        "budjet applicaton",  # Multiple typos
        "persoenlishes budget",  # German with ae->ä
        "assistence program"  # Typo
    ]
    
    print("Spell Checking Results:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nOriginal: '{query}'")
        
        check_results = checker.check_spelling(query)
        
        for result in check_results:
            if not result['is_correct']:
                print(f"  '{result['word']}' -> misspelled")
                if result['suggestions']:
                    print(f"    Suggestions:")
                    for sug in result['suggestions'][:3]:
                        print(f"      - {sug['suggestion']} (distance: {sug['distance']})")
        
        # Get full correction
        correction = checker.suggest_query_correction(query)
        if correction:
            print(f"  Suggested: '{correction}'")
```

---

## 🎯 Complete Autocomplete Service

### Unified Suggestion Engine

```python
# ios_core/search/autocomplete/service.py

from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class AutocompleteSuggestion:
    """Autocomplete suggestion with metadata"""
    text: str
    score: float
    source: str  # 'trie', 'popular', 'personal', 'corrected'
    metadata: Dict

class AutocompleteService:
    """
    Unified autocomplete service
    
    Combines:
    - Trie-based prefix matching
    - Popular queries
    - Spell checking
    - Personalization
    """
    
    def __init__(
        self,
        trie: AutocompleteTrie,
        popularity_tracker: QueryPopularityTracker,
        spell_checker: SpellChecker
    ):
        self.trie = trie
        self.popularity = popularity_tracker
        self.spell_checker = spell_checker
    
    def get_suggestions(
        self,
        prefix: str,
        limit: int = 10,
        user_id: Optional[int] = None,
        user_context: Optional[Dict] = None
    ) -> List[AutocompleteSuggestion]:
        """
        Get autocomplete suggestions
        
        Algorithm:
        1. Get trie suggestions (prefix match)
        2. Get popular queries (starting with prefix)
        3. Check spelling (suggest corrections)
        4. Merge and rank
        5. Personalize
        """
        start_time = time.time()
        
        prefix = prefix.lower().strip()
        
        if len(prefix) < 2:
            # Too short, return popular queries only
            return self._get_popular_suggestions(limit)
        
        suggestions = []
        
        # 1. Trie suggestions (exact prefix match)
        trie_results = self.trie.search(prefix, limit=limit)
        
        for result in trie_results:
            suggestions.append(AutocompleteSuggestion(
                text=result.text,
                score=result.score * 1.5,  # Boost trie results
                source='trie',
                metadata=result.metadata
            ))
        
        # 2. Popular queries (that start with prefix)
        popular_results = self.popularity.get_popular_queries(limit=100)
        
        for item in popular_results:
            query = item['query']
            
            if query.startswith(prefix) and query not in [s.text for s in suggestions]:
                suggestions.append(AutocompleteSuggestion(
                    text=query,
                    score=item['score'],
                    source='popular',
                    metadata={'frequency': item['score']}
                ))
        
        # 3. Spell checking (if no results or low confidence)
        if len(suggestions) < 3:
            correction = self.spell_checker.suggest_query_correction(prefix)
            
            if correction and correction != prefix:
                # Add corrected query
                suggestions.append(AutocompleteSuggestion(
                    text=correction,
                    score=10.0,  # High score for corrections
                    source='corrected',
                    metadata={'original': prefix}
                ))
        
        # 4. Merge and deduplicate
        seen = set()
        unique_suggestions = []
        
        for sug in suggestions:
            if sug.text not in seen:
                seen.add(sug.text)
                unique_suggestions.append(sug)
        
        # 5. Sort by score
        unique_suggestions.sort(key=lambda x: x.score, reverse=True)
        
        # 6. Personalize (if user context provided)
        if user_context:
            unique_suggestions = self._personalize_suggestions(
                unique_suggestions,
                user_context
            )
        
        # 7. Limit results
        final_suggestions = unique_suggestions[:limit]
        
        # Log performance
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"Autocomplete for '{prefix}': {len(final_suggestions)} suggestions "
            f"in {elapsed_ms:.1f}ms"
        )
        
        return final_suggestions
    
    def _get_popular_suggestions(self, limit: int) -> List[AutocompleteSuggestion]:
        """Get popular queries (for empty/short prefix)"""
        popular = self.popularity.get_popular_queries(limit=limit)
        
        return [
            AutocompleteSuggestion(
                text=item['query'],
                score=item['score'],
                source='popular',
                metadata={'frequency': item['score']}
            )
            for item in popular
        ]
    
    def _personalize_suggestions(
        self,
        suggestions: List[AutocompleteSuggestion],
        user_context: Dict
    ) -> List[AutocompleteSuggestion]:
        """
        Personalize suggestions based on user context
        
        Boosts:
        - User's recent queries
        - User's language preference
        - User's domain expertise
        """
        user_id = user_context.get('user_id')
        
        if not user_id:
            return suggestions
        
        # Get user's recent queries (from cache or DB)
        from ios_core.analytics.models import SearchQuery
        from django.utils import timezone
        from datetime import timedelta
        
        recent_queries = set(
            SearchQuery.objects.filter(
                user_id=user_id,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).values_list('normalized_query', flat=True)[:20]
        )
        
        # Boost matching queries
        for suggestion in suggestions:
            if suggestion.text in recent_queries:
                suggestion.score *= 1.3  # 30% boost
                suggestion.source = 'personal'
        
        # Re-sort
        suggestions.sort(key=lambda x: x.score, reverse=True)
        
        return suggestions


# API endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def autocomplete(request):
    """
    Autocomplete API endpoint
    
    GET /api/search/autocomplete?q=perso&limit=10
    """
    prefix = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    # Get service instance
    from ios_core.search.autocomplete import get_autocomplete_service
    service = get_autocomplete_service()
    
    # Get suggestions
    suggestions = service.get_suggestions(
        prefix=prefix,
        limit=limit,
        user_id=request.user.id if request.user.is_authenticated else None,
        user_context={
            'user_id': request.user.id if request.user.is_authenticated else None,
            'language': request.LANGUAGE_CODE
        }
    )
    
    # Format response
    return Response({
        'query': prefix,
        'suggestions': [
            {
                'text': s.text,
                'score': s.score,
                'source': s.source
            }
            for s in suggestions
        ]
    })
```

---

## ⚡ Performance Optimization

### Caching Strategy

```python
# ios_core/search/autocomplete/cache.py

from typing import List, Optional
from django.core.cache import cache
import hashlib
import logging

logger = logging.getLogger(__name__)

class AutocompleteCache:
    """
    Multi-level cache for autocomplete
    
    Levels:
    1. L1: In-memory (fastest, 1ms)
    2. L2: Redis (fast, 5ms)
    3. L3: Database (slow, 50ms)
    """
    
    def __init__(self):
        self.cache_ttl = {
            'l1': 300,   # 5 minutes
            'l2': 3600,  # 1 hour
        }
        self.prefix = "autocomplete:"
    
    def get(
        self,
        query: str,
        user_id: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """Get cached suggestions"""
        cache_key = self._generate_key(query, user_id)
        
        # Try L1 (in-memory)
        cached = cache.get(f"{self.prefix}l1:{cache_key}")
        if cached:
            logger.debug(f"L1 cache hit: {query}")
            return cached
        
        # Try L2 (Redis)
        cached = cache.get(f"{self.prefix}l2:{cache_key}")
        if cached:
            logger.debug(f"L2 cache hit: {query}")
            # Promote to L1
            cache.set(
                f"{self.prefix}l1:{cache_key}",
                cached,
                self.cache_ttl['l1']
            )
            return cached
        
        logger.debug(f"Cache miss: {query}")
        return None
    
    def set(
        self,
        query: str,
        suggestions: List[Dict],
        user_id: Optional[int] = None
    ):
        """Cache suggestions"""
        cache_key = self._generate_key(query, user_id)
        
        # Set in both levels
        cache.set(
            f"{self.prefix}l1:{cache_key}",
            suggestions,
            self.cache_ttl['l1']
        )
        
        cache.set(
            f"{self.prefix}l2:{cache_key}",
            suggestions,
            self.cache_ttl['l2']
        )
    
    def _generate_key(self, query: str, user_id: Optional[int]) -> str:
        """Generate cache key"""
        key_parts = [query.lower().strip()]
        
        if user_id:
            key_parts.append(f"user:{user_id}")
        
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]


# Performance monitoring
class AutocompleteMetrics:
    """Track autocomplete performance"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'avg_latency_ms': 0,
            'by_prefix_length': {}
        }
    
    def record_request(
        self,
        prefix: str,
        latency_ms: float,
        cache_hit: bool,
        suggestions_count: int
    ):
        """Record autocomplete request"""
        self.metrics['total_requests'] += 1
        
        if cache_hit:
            self.metrics['cache_hits'] += 1
        
        # Update average latency
        self.metrics['avg_latency_ms'] = (
            (self.metrics['avg_latency_ms'] * (self.metrics['total_requests'] - 1) + latency_ms)
            / self.metrics['total_requests']
        )
        
        # Track by prefix length
        prefix_len = len(prefix)
        if prefix_len not in self.metrics['by_prefix_length']:
            self.metrics['by_prefix_length'][prefix_len] = {
                'count': 0,
                'avg_latency': 0
            }
        
        stats = self.metrics['by_prefix_length'][prefix_len]
        stats['count'] += 1
        stats['avg_latency'] = (
            (stats['avg_latency'] * (stats['count'] - 1) + latency_ms)
            / stats['count']
        )
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        cache_hit_rate = (
            self.metrics['cache_hits'] / self.metrics['total_requests']
            if self.metrics['total_requests'] > 0 else 0
        )
        
        return {
            'total_requests': self.metrics['total_requests'],
            'cache_hit_rate': cache_hit_rate,
            'avg_latency_ms': self.metrics['avg_latency_ms'],
            'by_prefix_length': self.metrics['by_prefix_length']
        }
```

---

**Продолжение следует...**

Создано:
- ✅ Trie-based autocomplete with prefix search
- ✅ Query popularity tracking (global & trending)
- ✅ Spell checking with Levenshtein distance
- ✅ German-specific spell checker
- ✅ Unified autocomplete service
- ✅ Multi-level caching
- ✅ Performance metrics

**Следующие разделы:**
1. Real-time Monitoring & Alerts
2. Performance Tuning Guide
3. Deployment & Scaling Strategy

**Готовы продолжить с Monitoring?**