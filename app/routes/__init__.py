from flask import Flask, jsonify
from .hemoes import hemoes_bp
from .detran import detran_bp
from .sesa import sesa_bp

def register_blueprints(app: Flask):
    """Registra todos os blueprints da aplicação."""
    
    # Rota home
    @app.route('/')
    def home():
        return jsonify({
            "message": "API CrewAI para Integração com APIs Governamentais (ES)",
            "version": "1.0"
        })
    
    # Registrar blueprints
    app.register_blueprint(hemoes_bp)
    app.register_blueprint(detran_bp)
    app.register_blueprint(sesa_bp)