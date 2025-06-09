import json
from crewai.tools import BaseTool
from flask import current_app
from app.utils.helpers import json_dumps

class DetranSearchVehiclesTool(BaseTool):
    name: str = "detran_search_vehicles"
    description: str = "Busca veículos registrados no DETRAN para um CPF. Input: cpf (string)."
    
    def _run(self, cpf: str) -> str:
        result = current_app.clients['detran'].get_vehicles(cpf)
        return json_dumps(result)

class DetranFetchProfileTool(BaseTool):
    name: str = "detran_fetch_profile"
    description: str = "Busca o perfil completo de um cidadão. Requer user_id. Input: user_id (string)."
    
    def _run(self, user_id: str) -> str:
        result = current_app.clients['detran'].fetch_user_profile(user_id)
        return json_dumps(result)

class DetranAtualizarVeiculosTool(BaseTool):
    name: str = "detran_atualizar_veiculos"
    description: str = "Atualiza a lista de veículos no perfil de um cidadão. Inputs: user_id (string), veiculos (JSON string da lista de veículos)."
    
    def _run(self, user_id: str, veiculos: str) -> str:
        veiculos_data = json.loads(veiculos)
        result = current_app.clients['detran'].atualizar_veiculos(user_id, veiculos_data)
        return json_dumps(result)