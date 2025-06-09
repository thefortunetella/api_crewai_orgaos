import os

class Config:
    """Configurações da aplicação."""
    
    # API Base
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://api.es.gov.br')
    
    # OAuth2 Configuration
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Flask Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Timeouts
    REQUEST_TIMEOUT = 30
    
    # LLM Configuration
    LLM_TEMPERATURE = 0.2