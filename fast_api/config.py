from decouple import config

class Settings:
    PROJECT_NAME: str = "Golden Star Agency API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    USE_SQLITE: bool = config('USE_SQLITE', default=False, cast=bool)
    
    if USE_SQLITE:
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent
        db_path = root_dir / 'core_admin' / 'db.sqlite3'
        db_path_str = db_path.as_posix()
        DATABASE_URL: str = f"sqlite:///{db_path_str}"
    else:
        DATABASE_URL: str = config(
            'DATABASE_URL', 
            default='postgresql://postgres:postgres@localhost:5432/golden_star_db'
        )
    
    # Security
    JWT_SECRET_KEY: str = config('JWT_SECRET_KEY', default='super-secret-jwt-signing-key')
    JWT_ALGORITHM: str = "HS256"
    
    # AI Chatbot
    CLAUDE_API_KEY: str = config('CLAUDE_API_KEY', default='')
    GROQ_API_KEY: str = config('GROQ_API_KEY', default='')
    
    # Environment
    ENVIRONMENT: str = config('ENVIRONMENT', default='development')

settings = Settings()
