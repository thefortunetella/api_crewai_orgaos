from flask import Flask
from app.config import Config
from app.auth.manager import CompleteAuthenticationManager
from app.clients import HemoesClient, DetranClient, SesaClient
from app.agents.factory import AgentFactory
from app.routes import register_blueprints

def create_app():
    """Factory para criar e configurar uma instância da aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar componentes
    auth_manager = CompleteAuthenticationManager()
    
    # Registrar clientes
    app.clients = {
        'hemoes': HemoesClient(auth_manager),
        'detran': DetranClient(auth_manager),
        'sesa': SesaClient(auth_manager)
    }
    
    # Registrar agentes
    agent_factory = AgentFactory()
    app.agents = agent_factory.create_all_agents()
    
    # Registrar blueprints/rotas
    register_blueprints(app)
    
    return app