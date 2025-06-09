import json
from crewai.tools import BaseTool
from flask import current_app
from app.utils.helpers import json_dumps

class SesaGetMunicipiosTool(BaseTool):
    name: str = "sesa_get_municipios"
    description: str = "Lista todos os municípios disponíveis para agendamento."
    
    def _run(self) -> str:
        result = current_app.clients['sesa'].get_municipios()
        return json_dumps(result)

class SesaGetServicosTool(BaseTool):
    name: str = "sesa_get_servicos"
    description: str = "Lista todos os serviços disponíveis para agendamento."
    
    def _run(self) -> str:
        result = current_app.clients['sesa'].get_servicos()
        return json_dumps(result)

class SesaGetUnidadesTool(BaseTool):
    name: str = "sesa_get_unidades"
    description: str = "Lista unidades de atendimento baseado no município e serviço. Inputs: municipio_id (string), servico_id (string)."
    
    def _run(self, municipio_id: str, servico_id: str) -> str:
        result = current_app.clients['sesa'].get_unidades(municipio_id, servico_id)
        return json_dumps(result)

class SesaGetHorariosTool(BaseTool):
    name: str = "sesa_get_horarios"
    description: str = "Consulta horários disponíveis para uma unidade em uma data. Inputs: unidade_id (string), data (string YYYY-MM-DD)."
    
    def _run(self, unidade_id: str, data: str) -> str:
        result = current_app.clients['sesa'].get_horarios(unidade_id, data)
        return json_dumps(result)

class SesaGetSugestaoAgendamentoTool(BaseTool):
    name: str = "sesa_get_sugestao_agendamento"
    description: str = "Obtém sugestões de agendamento. Input: payload (JSON string com os critérios)."
    
    def _run(self, payload: str) -> str:
        payload_data = json.loads(payload)
        result = current_app.clients['sesa'].get_sugestao_agendamento(payload_data)
        return json_dumps(result)

class SesaReservarHorarioTool(BaseTool):
    name: str = "sesa_reservar_horario"
    description: str = "Realiza uma reserva de horário. Inputs: user_id (string), payload (JSON string da reserva)."
    
    def _run(self, user_id: str, payload: str) -> str:
        payload_data = json.loads(payload)
        payload_data['usuario'] = user_id
        result = current_app.clients['sesa'].reservar_horario(payload_data, user_id)
        return json_dumps(result)

class SesaCheckAgendamentoExistenteTool(BaseTool):
    name: str = "sesa_check_agendamento_existente"
    description: str = "Verifica agendamentos existentes para um usuário. Inputs: user_id (string), servico_id (string), ativo (boolean)."
    
    def _run(self, user_id: str, servico_id: str, ativo: bool = True) -> str:
        result = current_app.clients['sesa'].check_agendamento_existente(servico_id, user_id, ativo)
        return json_dumps(result)

class SesaCancelarAgendamentoTool(BaseTool):
    name: str = "sesa_cancelar_agendamento"
    description: str = "Cancela um agendamento existente. Inputs: user_id (string), agendamento_id (integer)."
    
    def _run(self, user_id: str, agendamento_id: int) -> str:
        result = current_app.clients['sesa'].cancelar_agendamento(agendamento_id, user_id)
        return json_dumps(result)