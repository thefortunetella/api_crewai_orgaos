from flask import Blueprint, request, jsonify, current_app
from app.utils.helpers import process_query

hemoes_bp = Blueprint('hemoes', __name__)

@hemoes_bp.route('/hemoes', methods=['POST'])
def hemoes_endpoint():
    """Endpoint para consultas do HEMOES."""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "Campo 'query' é obrigatório."}), 400
    
    result = process_query(
        current_app.agents['hemoes'],
        data['query'],
        'HEMOES',
        data.get('user_context')
    )
    
    return jsonify(result)