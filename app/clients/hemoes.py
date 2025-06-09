from typing import Dict, Any
from .base import BaseApiClient

class HemoesClient(BaseApiClient):
    """Cliente para APIs de Doação de Sangue (Hemoes)."""
    
    def get_doador(self, cpf: str) -> Dict[str, Any]:
        """Busca informações de um doador pelo CPF."""
        params = {
            'fields': '*.*',
            'filter[cpf][_eq]': self._clean_cpf(cpf)
        }
        
        endpoint = f"{self.base_url}/api/hemoes/items/doador"
        
        return self._make_request(
            "get",
            endpoint,
            headers=self._get_basic_headers(),
            params=params
        )

    def get_doacao(self, doacao_id: int) -> Dict[str, Any]:
        """Busca detalhes de uma doação específica pelo ID."""
        params = {
            'fields': '*.*',
            'filter[id][_eq]': doacao_id
        }
        
        endpoint = f"{self.base_url}/api/hemoes/items/doacao"
        
        return self._make_request(
            "get",
            endpoint,
            headers=self._get_basic_headers(),
            params=params
        )