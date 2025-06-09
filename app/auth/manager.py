import os
import base64
import time
import logging
from typing import Dict, Optional
import requests
from app.models.types import TokenResponse

logger = logging.getLogger(__name__)

# --- Constantes ---
HEADER_AUTH = 'Authorization'
HEADER_CONTENT_TYPE = 'Content-Type'
URL_ENCODED = 'application/x-www-form-urlencoded'
GRANT_TYPE_CLIENT_CREDENTIALS = 'client_credentials'
GRANT_TYPE_REFRESH_TOKEN = 'refresh_token'
GRANT_TYPE_AUTH_CODE = 'authorization_code'

class CompleteAuthenticationManager:
    """Gerenciador de autenticação para todos os tipos de auth da API."""
    
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'https://api.es.gov.br')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self._system_tokens: Dict[str, str] = {}
        self._system_token_expires: Dict[str, float] = {}
        self._user_tokens: Dict[str, str] = {}
        self._user_token_expires: Dict[str, float] = {}
        self._refresh_tokens: Dict[str, str] = {}

    def get_system_token(self, scope: str) -> Optional[str]:
        """Obtém token de sistema para escopo específico."""
        if (scope in self._system_tokens and 
            time.time() < self._system_token_expires.get(scope, 0)):
            return self._system_tokens[scope]
        
        if not self.client_id or not self.client_secret:
            logger.critical(f"CLIENT_ID e CLIENT_SECRET são obrigatórios (escopo: {scope}).")
            return None
        
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                HEADER_AUTH: f'Basic {encoded_credentials}',
                HEADER_CONTENT_TYPE: URL_ENCODED
            }
            
            data = {
                'grant_type': GRANT_TYPE_CLIENT_CREDENTIALS,
                'scope': scope
            }
            
            response = requests.post(
                f"{self.base_url}/api/acessocidadao/is/connect/token",
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data: TokenResponse = response.json()
            self._system_tokens[scope] = token_data['access_token']
            self._system_token_expires[scope] = (
                time.time() + token_data.get('expires_in', 3600) - 60
            )
            
            logger.info(f"Token de sistema obtido com sucesso para escopo: {scope}")
            return self._system_tokens[scope]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição ao obter token de sistema ({scope}): {e}")
            return None

    def get_user_token(self, user_id: str, authorization_code: Optional[str] = None, 
                      refresh_token_val: Optional[str] = None) -> Optional[str]:
        """Obtém token de usuário."""
        if (user_id in self._user_tokens and 
            time.time() < self._user_token_expires.get(user_id, 0)):
            return self._user_tokens[user_id]
        
        current_refresh_token = refresh_token_val or self._refresh_tokens.get(user_id)
        if current_refresh_token:
            token = self._refresh_user_token(user_id, current_refresh_token)
            if token:
                return token
        
        if authorization_code:
            return self._get_new_user_token(user_id, authorization_code)
        
        logger.warning(f"Não foi possível obter token de usuário para user_id: {user_id}.")
        return None

    def _update_user_token_data(self, user_id: str, token_data: TokenResponse):
        """Atualiza dados do token de usuário."""
        self._user_tokens[user_id] = token_data['access_token']
        self._user_token_expires[user_id] = (
            time.time() + token_data.get('expires_in', 3600) - 60
        )
        
        if 'refresh_token' in token_data and token_data['refresh_token']:
            self._refresh_tokens[user_id] = token_data['refresh_token']

    def _get_new_user_token(self, user_id: str, authorization_code: str) -> Optional[str]:
        """Obtém novo token de usuário com código de autorização."""
        data = {
            'grant_type': GRANT_TYPE_AUTH_CODE,
            'code': authorization_code,
            'redirect_uri': os.getenv('REDIRECT_URI')
        }
        return self._fetch_user_token(user_id, data)

    def _refresh_user_token(self, user_id: str, refresh_token: str) -> Optional[str]:
        """Atualiza token de usuário usando refresh token."""
        data = {
            'grant_type': GRANT_TYPE_REFRESH_TOKEN,
            'refresh_token': refresh_token
        }
        token = self._fetch_user_token(user_id, data)
        
        if not token and user_id in self._refresh_tokens:
            del self._refresh_tokens[user_id]
        
        return token

    def _fetch_user_token(self, user_id: str, data: Dict[str, str]) -> Optional[str]:
        """Busca token de usuário na API."""
        if not self.client_id or not self.client_secret:
            return None
        
        try:
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                HEADER_AUTH: f'Basic {encoded_credentials}',
                HEADER_CONTENT_TYPE: URL_ENCODED
            }
            
            response = requests.post(
                f"{self.base_url}/api/acessocidadao/is/connect/token",
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data: TokenResponse = response.json()
            self._update_user_token_data(user_id, token_data)
            return self._user_tokens[user_id]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição ao obter token de usuário ({user_id}): {e}")
            return None