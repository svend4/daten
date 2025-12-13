# ios_core/services/search.py

from ..cache import cached

class SearchService:
    
    @cached(ttl=600, key_prefix="search")
    async def search(
        self,
        query: str,
        domain_name: Optional[str] = None,
        search_type: str = "hybrid",
        limit: int = 10,
        offset: int = 0
    ) -> dict:
        """Search with caching"""
        # Original search logic...
        pass