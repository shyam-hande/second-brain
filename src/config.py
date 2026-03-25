from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    
    # Model settings
    model_name: str = "claude-sonnet-4-20250514"
    
    # RAG settings
    chroma_db_path: str = "./data/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k_results: int = 3
    
    # Memory settings
    memory_db_path: str = "./data/memory.json"
    max_conversation_history: int = 20
    
    # Data paths
    notes_path: str = "./data/notes"
    transcriptions_path: str = "./data/transcriptions"
    recipes_path: str = "./data/recipes"
    
    class Config:
        env_file = ".env"


# Singleton
settings = Settings()