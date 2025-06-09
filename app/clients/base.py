import logging
import re
from typing import Dict, Any, TYPE_CHECKING
import requests

if TYPE_CHECKING:
    from app.auth.manager import CompleteAuthenticationManager

logger = logging.getLogger(__name__)

APPLICATION_JSON = 'application/json'

class BaseApiClient:
    """Classe base para clientes de API com lógica de requisição centralizada."""
    
    def __init__(self, auth_manager: "CompleteAuthenticationManager"):
        self.base_url = auth_manager.base_url
        self.auth_manager = auth_manager

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Método central para fazer requisições e tratar erros comuns."""
        try:
            response = requests.request(method, endpoint, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
        except requests.exceptions.Timeout:
            logger.error(f"Timeout na chamada para {endpoint}")
            return {
                "error": "Timeout",
                "message": "A requisição demorou muito para responder."
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP em {endpoint}: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"HTTP Error {e.response.status_code}",
                "message": "Erro na comunicação com o serviço."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição para {endpoint}: {e}")
            return {
                "error": str(e),
                "message": "Não foi possível conectar ao serviço."
            }

    def _clean_cpf(self, cpf: str) -> str:
        """Remove caracteres não numéricos do CPF."""
        return re.sub(r'[^\d]', '', cpf)

    def _get_basic_headers(self) -> Dict[str, str]:
        """Retorna headers básicos para requisições."""
        return {
            'User-Agent': 'CrewAI-GovES-Client/1.0',
            'Accept': APPLICATION_JSON
        }