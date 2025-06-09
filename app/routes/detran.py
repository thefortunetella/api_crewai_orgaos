from flask import Blueprint, request, jsonify, current_app
from app.utils.helpers import process_query

detran_bp = Blueprint('detran', __name__)

@detran_bp.route('/detran', methods=['POST'])
def detran_endpoint():
    """Endpoint para consultas do DETRAN."""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "Campo 'query' é obrigatório."}), 400
    
    result = process_query(
        current_app.agents['detran'],
        data['query'],
        'DETRAN',
        data.get('user_context')
    )
    
    return jsonify(result)