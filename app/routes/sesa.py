from flask import Blueprint, request, jsonify, current_app
from app.utils.helpers import process_query

sesa_bp = Blueprint('sesa', __name__)

@sesa_bp.route('/sesa', methods=['POST'])
def sesa_endpoint():
    """Endpoint para consultas da SESA."""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "Campo 'query' é obrigatório."}), 400
    
    result = process_query(
        current_app.agents['sesa'],
        data['query'],
        'SESA',
        data.get('user_context')
    )
    
    return jsonify(result)