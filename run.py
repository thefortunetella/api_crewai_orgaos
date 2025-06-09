import os
import logging
from dotenv import load_dotenv
from app import create_app

# --- Configuração de Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Ponto de entrada principal da aplicação."""
    load_dotenv()
    
    # Validações críticas
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("!!! OPENAI_API_KEY não configurada. A aplicação não funcionará. !!!")
    
    if not os.getenv("CLIENT_ID") or not os.getenv("CLIENT_SECRET"):
        logger.critical("!!! CLIENT_ID e/ou CLIENT_SECRET não configurados. A autenticação OAuth2 falhará. !!!")
    
    # Criar e executar aplicação
    app = create_app()
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()