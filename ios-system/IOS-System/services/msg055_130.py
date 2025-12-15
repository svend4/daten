"""
Configuration - UPDATED with ML and search settings
"""

# ... (existing code)

class Settings(BaseSettings):
    # ... (existing settings)
    
    # ML Services
    bert_service_url: str = "http://localhost:8001"
    sentence_transformers_url: str = "http://localhost:8003"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Neural Search
    default_semantic_weight: float = 0.6
    default_keyword_weight: float = 0.4
    enable_query_expansion: bool = True
    enable_personalization: bool = True
    
    # Multi-language
    default_language: str = "de"
    supported_languages: List[str] = ["de", "ru", "en"]
    enable_auto_translation: bool = True
    
    # Search Analytics
    track_search_clicks: bool = True
    track_search_satisfaction: bool = True
    analytics_retention_days: int = 90
    
    class Config:
        env_file = ".env"

# ... (rest of existing code)