from crewai.tools import BaseTool
from flask import current_app
from app.utils.helpers import json_dumps

class HemoesGetDoadorTool(BaseTool):
    name: str = "hemoes_get_doador"
    description: str = "Busca informações de um doador de sangue pelo CPF. Input: cpf (string)."
    
    def _run(self, cpf: str) -> str:
        result = current_app.clients['hemoes'].get_doador(cpf)
        return json_dumps(result)

class HemoesGetDoacaoTool(BaseTool):
    name: str = "hemoes_get_doacao"
    description: str = "Busca detalhes de uma doação específica pelo ID. Input: doacao_id (integer)."
    
    def _run(self, doacao_id: int) -> str:
        result = current_app.clients['hemoes'].get_doacao(doacao_id)
        return json_dumps(result)