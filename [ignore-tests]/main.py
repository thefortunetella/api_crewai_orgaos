import os
import re
import base64
import time
import json
from typing import Optional, Dict, Any, List, TypedDict

from flask import Flask, request, jsonify, current_app
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
import requests
from dotenv import load_dotenv
import logging

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# --- Constantes ---
HEADER_AUTH = 'Authorization'
HEADER_CONTENT_TYPE = 'Content-Type'
URL_ENCODED = 'application/x-www-form-urlencoded'
APPLICATION_JSON = 'application/json'
GRANT_TYPE_CLIENT_CREDENTIALS = 'client_credentials'
GRANT_TYPE_REFRESH_TOKEN = 'refresh_token'
GRANT_TYPE_AUTH_CODE = 'authorization_code'
SCOPE_DETRAN_VEHICLES = 'detran_vehicles'
SOURCE_DETRAN = 'DETRAN'
SERVICE_CODE_MEUS_VEICULOS = 'meusVeiculos'

# --- Estruturas de Dados Tipadas (TypedDict) ---
class TokenResponse(TypedDict): access_token: str; expires_in: int; refresh_token: Optional[str]
class Veiculo(TypedDict): id: str; plate: str; model: str; brandLogo: str

class ServiceCodeDataItem(TypedDict):
    serviceCode: str
    data: Dict[str, List[Veiculo]]

class AtualizarVeiculosPayload(TypedDict):
    source: str
    serviceCodesData: List[ServiceCodeDataItem]

class ReservaHorarioPayload(TypedDict):
    usuario: str
    servico: str
    data: str
    hora: str
    unidade: str
    nome_do_usuario: str

class SugestaoAgendamentoPayload(TypedDict): dataNascimento: Optional[str]; servico: str; cep: Optional[str]

# --- Classes de Cliente da API ---
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
            logger.error(f"Timeout na chamada para {endpoint}"); return {"error": "Timeout", "message": "A requisição demorou muito para responder."}
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP em {endpoint}: {e.response.status_code} - {e.response.text}"); return {"error": f"HTTP Error {e.response.status_code}", "message": "Erro na comunicação com o serviço."}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição para {endpoint}: {e}"); return {"error": str(e), "message": "Não foi possível conectar ao serviço."}

class CompleteAuthenticationManager:
    """Gerenciador de autenticação para todos os tipos de auth da API."""
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'https://api.es.gov.br')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self._system_tokens: Dict[str, str] = {}; self._system_token_expires: Dict[str, float] = {}
        self._user_tokens: Dict[str, str] = {}; self._user_token_expires: Dict[str, float] = {}
        self._refresh_tokens: Dict[str, str] = {}

    def get_system_token(self, scope: str) -> Optional[str]:
        if scope in self._system_tokens and time.time() < self._system_token_expires.get(scope, 0): return self._system_tokens[scope]
        if not self.client_id or not self.client_secret: logger.critical(f"CLIENT_ID e CLIENT_SECRET são obrigatórios (escopo: {scope})."); return None
        try:
            credentials = f"{self.client_id}:{self.client_secret}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers = {HEADER_AUTH: f'Basic {encoded_credentials}', HEADER_CONTENT_TYPE: URL_ENCODED}
            data = {'grant_type': GRANT_TYPE_CLIENT_CREDENTIALS, 'scope': scope}
            response = requests.post(f"{self.base_url}/api/acessocidadao/is/connect/token", headers=headers, data=data, timeout=30)
            response.raise_for_status()
            token_data: TokenResponse = response.json()
            self._system_tokens[scope] = token_data['access_token']; self._system_token_expires[scope] = time.time() + token_data.get('expires_in', 3600) - 60
            logger.info(f"Token de sistema (getToken) obtido com sucesso para escopo: {scope}"); return self._system_tokens[scope]
        except requests.exceptions.RequestException as e: logger.error(f"Erro na requisição ao obter token de sistema ({scope}): {e}"); return None

    def get_user_token(self, user_id: str, authorization_code: Optional[str] = None, refresh_token_val: Optional[str] = None) -> Optional[str]:
        if user_id in self._user_tokens and time.time() < self._user_token_expires.get(user_id, 0): return self._user_tokens[user_id]
        current_refresh_token = refresh_token_val or self._refresh_tokens.get(user_id)
        if current_refresh_token:
            token = self._refresh_user_token(user_id, current_refresh_token)
            if token: return token
        if authorization_code: return self._get_new_user_token(user_id, authorization_code)
        logger.warning(f"Não foi possível obter token de usuário para user_id: {user_id}."); return None

    def _update_user_token_data(self, user_id: str, token_data: TokenResponse):
        self._user_tokens[user_id] = token_data['access_token']; self._user_token_expires[user_id] = time.time() + token_data.get('expires_in', 3600) - 60
        if 'refresh_token' in token_data and token_data['refresh_token']: self._refresh_tokens[user_id] = token_data['refresh_token']

    def _get_new_user_token(self, user_id: str, authorization_code: str) -> Optional[str]:
        data = {'grant_type': GRANT_TYPE_AUTH_CODE, 'code': authorization_code, 'redirect_uri': os.getenv('REDIRECT_URI')}; return self._fetch_user_token(user_id, data)

    def _refresh_user_token(self, user_id: str, refresh_token: str) -> Optional[str]:
        data = {'grant_type': GRANT_TYPE_REFRESH_TOKEN, 'refresh_token': refresh_token}; token = self._fetch_user_token(user_id, data)
        if not token and user_id in self._refresh_tokens: del self._refresh_tokens[user_id]
        return token

    def _fetch_user_token(self, user_id: str, data: Dict[str, str]) -> Optional[str]:
        if not self.client_id or not self.client_secret: return None
        try:
            credentials = f"{self.client_id}:{self.client_secret}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers = {HEADER_AUTH: f'Basic {encoded_credentials}', HEADER_CONTENT_TYPE: URL_ENCODED}
            response = requests.post(f"{self.base_url}/api/acessocidadao/is/connect/token", headers=headers, data=data, timeout=30)
            response.raise_for_status(); token_data: TokenResponse = response.json(); self._update_user_token_data(user_id, token_data); return self._user_tokens[user_id]
        except requests.exceptions.RequestException as e: logger.error(f"Erro na requisição ao obter token de usuário ({user_id}): {e}"); return None

class HemoesClient(BaseApiClient):
    """Cliente para APIs de Doação de Sangue (Hemoes)."""
    def _get_auth_headers(self) -> Dict[str, str]: return {'User-Agent': 'CrewAI-GovES-Client/1.0', 'Accept': APPLICATION_JSON}
    def _clean_cpf(self, cpf: str) -> str: return re.sub(r'[^\d]', '', cpf)
    def get_doador(self, cpf: str) -> Dict[str, Any]:
        params = {'fields': '*.*', 'filter[cpf][_eq]': self._clean_cpf(cpf)}; endpoint = f"{self.base_url}/api/hemoes/items/doador"; return self._make_request("get", endpoint, headers=self._get_auth_headers(), params=params)
    def get_doacao(self, doacao_id: int) -> Dict[str, Any]:
        params = {'fields': '*.*', 'filter[id][_eq]': doacao_id}; endpoint = f"{self.base_url}/api/hemoes/items/doacao"; return self._make_request("get", endpoint, headers=self._get_auth_headers(), params=params)

class DetranClient(BaseApiClient):
    """Cliente para APIs do DETRAN."""
    def _clean_cpf(self, cpf: str) -> str: return re.sub(r'[^\d]', '', cpf)
    def _get_auth_header(self, token: str) -> Dict[str, str]: return {HEADER_AUTH: f'Bearer {token}', 'User-Agent': 'CrewAI-GovES-Client/1.0', 'Accept': APPLICATION_JSON}
    def get_vehicles(self, cpf: str) -> Dict[str, Any]:
        system_token = self.auth_manager.get_system_token(scope=SCOPE_DETRAN_VEHICLES)
        if not system_token: return {"error": "Authentication Error", "message": "Token de sistema para DETRAN não obtido."}
        headers = self._get_auth_header(system_token); params = {'cpfAcessoCidadao': self._clean_cpf(cpf)}; endpoint = f"{self.base_url}/api/portalinteligente/veiculo/v1/obter"; return self._make_request("get", endpoint, headers=headers, params=params)
    def fetch_user_profile(self, user_id: str, user_token_override: Optional[str] = None) -> Dict[str, Any]:
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        if not user_token: return {"error": "Authentication Error", "message": f"Token de usuário para DETRAN (user_id: {user_id}) não obtido."}
        headers = self._get_auth_header(user_token); endpoint = f"{self.base_url}/v1/profile"; return self._make_request("get", endpoint, headers=headers)
    def atualizar_veiculos(self, user_id: str, veiculos: List[Veiculo], user_token_override: Optional[str] = None) -> Dict[str, Any]:
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        if not user_token: return {"error": "Authentication Error", "message": f"Token de usuário para DETRAN (user_id: {user_id}) não obtido."}
        headers = self._get_auth_header(user_token)
        payload: AtualizarVeiculosPayload = {
            "source": SOURCE_DETRAN,
            "serviceCodesData": [
                {
                    "serviceCode": SERVICE_CODE_MEUS_VEICULOS,
                    "data": {"veiculos": veiculos}
                }
            ]
        }
        endpoint = f"{self.base_url}/v1/profile/external-data"; return self._make_request("patch", endpoint, headers=headers, json=payload)

class SesaClient(BaseApiClient):
    """Cliente para APIs da SESA."""
    def _get_auth_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        headers = {'User-Agent': 'CrewAI-GovES-Client/1.0', 'Accept': APPLICATION_JSON}
        if user_token: headers[HEADER_AUTH] = f'Bearer {user_token}'
        return headers
    def get_municipios(self) -> Dict[str, Any]: return self._make_request("get", f"{self.base_url}/api/agendamento/municipios", headers=self._get_auth_headers())
    def get_servicos(self) -> Dict[str, Any]: return self._make_request("get", f"{self.base_url}/api/agendamento/servicos", headers=self._get_auth_headers())
    def get_unidades(self, municipio_id: str, servico_id: str) -> Dict[str, Any]: params = {'municipio_id': municipio_id, 'servico_id': servico_id}; return self._make_request("get", f"{self.base_url}/api/agendamento/unidades", headers=self._get_auth_headers(), params=params)
    
    def get_horarios(self, unidade_id: str, data: str) -> Dict[str, Any]:
        params = {'unidade': unidade_id, 'data': data}
        return self._make_request("get", f"{self.base_url}/api/agendamento/horarios-disponiveis", headers=self._get_auth_headers(), params=params)

    def get_sugestao_agendamento(self, payload: SugestaoAgendamentoPayload) -> Dict[str, Any]: return self._make_request("post", f"{self.base_url}/api/agendamento/sugestao-agendamento", headers=self._get_auth_headers(), json=payload)
    
    def reservar_horario(self, payload: ReservaHorarioPayload, user_id: str, user_token_override: Optional[str] = None) -> Dict[str, Any]:
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        if not user_token: return {"error": "Authentication Error", "message": "A reserva requer autenticação de usuário."}
        return self._make_request("post", f"{self.base_url}/api/agendamento/reservar", headers=self._get_auth_headers(user_token), json=payload)
    
    def check_agendamento_existente(self, servico_id: str, user_id: str, ativo: bool, user_token_override: Optional[str] = None) -> Dict[str, Any]:
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        if not user_token: return {"error": "Authentication Error", "message": "A verificação de agendamentos requer autenticação de usuário."}
        params = {'servico': servico_id, 'ativo': str(ativo).lower()}
        return self._make_request("get", f"{self.base_url}/api/agendamento/meus-agendamentos", headers=self._get_auth_headers(user_token), params=params)

    def cancelar_agendamento(self, agendamento_id: int, user_id: str, user_token_override: Optional[str] = None) -> Dict[str, Any]:
        user_token = user_token_override or self.auth_manager.get_user_token(user_id)
        if not user_token: return {"error": "Authentication Error", "message": "O cancelamento de agendamento requer autenticação de usuário."}
        return self._make_request("post", f"{self.base_url}/api/agendamento/meus-agendamentos/{agendamento_id}/cancelar", headers=self._get_auth_headers(user_token))

# --- Ferramentas CrewAI ---
def _json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2)

class HemoesGetDoadorTool(BaseTool):
    name: str = "hemoes_get_doador"
    description: str = "Busca informações de um doador de sangue pelo CPF. Input: cpf (string)."
    def _run(self, cpf: str) -> str:
        return _json_dumps(current_app.clients['hemoes'].get_doador(cpf))

class HemoesGetDoacaoTool(BaseTool):
    name: str = "hemoes_get_doacao"
    description: str = "Busca detalhes de uma doação específica pelo ID. Input: doacao_id (integer)."
    def _run(self, doacao_id: int) -> str:
        return _json_dumps(current_app.clients['hemoes'].get_doacao(doacao_id))

class DetranSearchVehiclesTool(BaseTool):
    name: str = "detran_search_vehicles"
    description: str = "Busca veículos registrados no DETRAN para um CPF. Input: cpf (string)."
    def _run(self, cpf: str) -> str:
        return _json_dumps(current_app.clients['detran'].get_vehicles(cpf))

class DetranFetchProfileTool(BaseTool):
    name: str = "detran_fetch_profile"
    description: str = "Busca o perfil completo de um cidadão. Requer user_id. Input: user_id (string)."
    def _run(self, user_id: str) -> str:
        return _json_dumps(current_app.clients['detran'].fetch_user_profile(user_id))

class DetranAtualizarVeiculosTool(BaseTool):
    name: str = "detran_atualizar_veiculos"
    description: str = "Atualiza a lista de veículos no perfil de um cidadão. Inputs: user_id (string), veiculos (JSON string da lista de veículos)."
    def _run(self, user_id: str, veiculos: str) -> str:
        return _json_dumps(current_app.clients['detran'].atualizar_veiculos(user_id, json.loads(veiculos)))

class SesaGetMunicipiosTool(BaseTool):
    name: str = "sesa_get_municipios"
    description: str = "Lista todos os municípios disponíveis para agendamento."
    def _run(self) -> str:
        return _json_dumps(current_app.clients['sesa'].get_municipios())

class SesaGetServicosTool(BaseTool):
    name: str = "sesa_get_servicos"
    description: str = "Lista todos os serviços disponíveis para agendamento."
    def _run(self) -> str:
        return _json_dumps(current_app.clients['sesa'].get_servicos())

class SesaGetUnidadesTool(BaseTool):
    name: str = "sesa_get_unidades"
    description: str = "Lista unidades de atendimento baseado no município e serviço. Inputs: municipio_id (string), servico_id (string)."
    def _run(self, municipio_id: str, servico_id: str) -> str:
        return _json_dumps(current_app.clients['sesa'].get_unidades(municipio_id, servico_id))

class SesaGetHorariosTool(BaseTool):
    name: str = "sesa_get_horarios"
    description: str = "Consulta horários disponíveis para uma unidade em uma data. Inputs: unidade_id (string), data (string OrderedDict-MM-DD)."
    def _run(self, unidade_id: str, data: str) -> str:
        return _json_dumps(current_app.clients['sesa'].get_horarios(unidade_id, data))

class SesaGetSugestaoAgendamentoTool(BaseTool):
    name: str = "sesa_get_sugestao_agendamento"
    description: str = "Obtém sugestões de agendamento. Input: payload (JSON string com os critérios)."
    def _run(self, payload: str) -> str:
        return _json_dumps(current_app.clients['sesa'].get_sugestao_agendamento(json.loads(payload)))

class SesaReservarHorarioTool(BaseTool):
    name: str = "sesa_reservar_horario"
    description: str = "Realiza uma reserva de horário. Inputs: user_id (string), payload (JSON string da reserva)."
    def _run(self, user_id: str, payload: str) -> str:
        payload_data = json.loads(payload)
        payload_data['usuario'] = user_id
        return _json_dumps(current_app.clients['sesa'].reservar_horario(payload_data, user_id))

class SesaCheckAgendamentoExistenteTool(BaseTool):
    name: str = "sesa_check_agendamento_existente"
    description: str = "Verifica agendamentos existentes para um usuário. Inputs: user_id (string), servico_id (string), ativo (boolean)."
    def _run(self, user_id: str, servico_id: str, ativo: bool = True) -> str:
        return _json_dumps(current_app.clients['sesa'].check_agendamento_existente(servico_id, user_id, ativo))

class SesaCancelarAgendamentoTool(BaseTool):
    name: str = "sesa_cancelar_agendamento"
    description: str = "Cancela um agendamento existente. Inputs: user_id (string), agendamento_id (integer)."
    def _run(self, user_id: str, agendamento_id: int) -> str:
        return _json_dumps(current_app.clients['sesa'].cancelar_agendamento(agendamento_id, user_id))

# --- Lógica da Aplicação e Rotas Flask ---
def process_query(agent: Agent, query: str, orgao: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    task = Task(
        description=(
            f"Processe a consulta do usuário sobre {orgao}: '{query}'. "
            f"Use as ferramentas disponíveis para encontrar a informação. "
            f"O contexto do usuário é: {user_context}."
        ),
        agent=agent,
        expected_output=(
            "Uma resposta final, clara e concisa em português, diretamente para o usuário. "
            "A resposta deve conter apenas a informação solicitada, sem incluir pensamentos internos, "
            "nomes de ferramentas ou logs de depuração. Se não encontrar a informação, "
            "informe educadamente que não foi possível obter os dados."
        )
    )
    try:
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff(inputs=user_context or {})
        return {"success": True, "response": str(result)}
    except Exception as e:
        logger.error(f"Erro crítico ao processar consulta para {orgao}: {e}", exc_info=True)
        return {"success": False, "error": "Ocorreu um erro interno ao processar sua solicitação."}

def create_app():
    """Cria e configura uma instância da aplicação Flask (Factory Pattern)."""
    app = Flask(__name__)
    auth_manager = CompleteAuthenticationManager()
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), api_key=os.getenv("OPENAI_API_KEY"), temperature=0.2)
    
    app.clients = {'hemoes': HemoesClient(auth_manager), 'detran': DetranClient(auth_manager), 'sesa': SesaClient(auth_manager)}
    
    app.agents = {
        'hemoes': Agent(
            role='Assistente Virtual do HEMOES',
            goal='Fornecer informações sobre doadores e doações de sangue de forma clara e em português.',
            backstory=(
                "Você é um assistente virtual especializado nos serviços do HEMOES. "
                "Sua principal função é ajudar os usuários a consultar informações sobre doadores por CPF e detalhes de doações por ID. "
                "Responda sempre em português do Brasil e de maneira amigável."
            ),
            llm=llm, tools=[HemoesGetDoadorTool(), HemoesGetDoacaoTool()], verbose=True, allow_delegation=False
        ),
        'detran': Agent(
            role='Assistente Virtual do DETRAN-ES',
            goal='Fornecer informações sobre veículos e perfis de cidadãos, sempre em português.',
            backstory=(
                "Você é um assistente virtual especializado nos serviços do DETRAN do Espírito Santo. "
                "Você utiliza ferramentas para consultar veículos, perfis de usuários e atualizar dados. "
                "Sua comunicação deve ser clara, objetiva e estritamente em português do Brasil."
            ),
            llm=llm, tools=[DetranSearchVehiclesTool(), DetranFetchProfileTool(), DetranAtualizarVeiculosTool()], verbose=True, allow_delegation=False
        ),
        'sesa': Agent(
            role='Assistente Virtual de Saúde Pública',
            goal='Ajudar usuários a encontrar informações e a gerenciar agendamentos de saúde na SESA, respondendo em português.',
            backstory=(
                "Você é um assistente virtual da Secretaria de Saúde (SESA), projetado para facilitar o acesso aos serviços. "
                "Você pode listar municípios e serviços, encontrar unidades, verificar horários, obter sugestões, e ajudar a realizar ou cancelar agendamentos. "
                "Seja sempre prestativo e responda em português do Brasil."
            ),
            llm=llm, tools=[
                SesaGetMunicipiosTool(), SesaGetServicosTool(), SesaGetUnidadesTool(), 
                SesaGetHorariosTool(), SesaGetSugestaoAgendamentoTool(), SesaReservarHorarioTool(), 
                SesaCheckAgendamentoExistenteTool(), SesaCancelarAgendamentoTool()
            ], verbose=True, allow_delegation=False
        )
    }

    def _handle_request(orgao_name: str):
        data = request.get_json();
        if not data or 'query' not in data: return jsonify({"error": "Campo 'query' é obrigatório."}), 400
        return jsonify(process_query(current_app.agents[orgao_name], data['query'], orgao_name.upper(), data.get('user_context')))

    @app.route('/')
    def home(): return jsonify({"message": "API CrewAI para Integração com APIs Governamentais (ES)", "version": "1.0"})
    @app.route('/hemoes', methods=['POST'])
    def hemoes_endpoint(): return _handle_request('hemoes')
    @app.route('/detran', methods=['POST'])
    def detran_endpoint(): return _handle_request('detran')
    @app.route('/sesa', methods=['POST'])
    def sesa_endpoint(): return _handle_request('sesa')

    return app

if __name__ == '__main__':
    if not os.getenv("OPENAI_API_KEY"): logger.critical("!!! OPENAI_API_KEY não configurada. A aplicação não funcionará. !!!")
    if not os.getenv("CLIENT_ID") or not os.getenv("CLIENT_SECRET"): logger.critical("!!! CLIENT_ID e/ou CLIENT_SECRET não configurados. A autenticação OAuth2 falhará. !!!")
    app = create_app()
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')