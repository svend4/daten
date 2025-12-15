"""
Configuration - UPDATED with GPT settings
"""

# ... (existing code)

class Settings(BaseSettings):
    # ... (existing settings)
    
    # OpenAI / GPT
    openai_api_key: str
    gpt_model: str = "gpt-4-turbo"
    gpt_temperature: float = 0.7
    gpt_max_tokens: int = 2000
    
    # Cost limits (USD)
    gpt_daily_cost_limit: float = 50.0
    gpt_monthly_cost_limit: float = 1000.0
    
    class Config:
        env_file = ".env"

# ... (rest of existing code)