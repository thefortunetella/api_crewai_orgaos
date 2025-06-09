import os
from typing import Dict
from crewai import Agent
from langchain_openai import ChatOpenAI
from app.config import Config
from app.tools import (
    HemoesGetDoadorTool, HemoesGetDoacaoTool,
    DetranSearchVehiclesTool, DetranFetchProfileTool, DetranAtualizarVeiculosTool,
    SesaGetMunicipiosTool, SesaGetServicosTool, SesaGetUnidadesTool,
    SesaGetHorariosTool, SesaGetSugestaoAgendamentoTool, SesaReservarHorarioTool,
    SesaCheckAgendamentoExistenteTool, SesaCancelarAgendamentoTool
)

class AgentFactory:
    """Factory para criar agentes CrewAI."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            api_key=Config.OPENAI_API_KEY,
            temperature=Config.LLM_TEMPERATURE
        )

    def create_hemoes_agent(self) -> Agent:
        """Cria agente para HEMOES."""
        return Agent(
            role='Assistente Virtual do HEMOES',
            goal='Fornecer informações sobre doadores e doações de sangue de forma clara e em português.',
            backstory=(
                "Você é um assistente virtual especializado nos serviços do HEMOES. "
                "Sua principal função é ajudar os usuários a consultar informações sobre doadores por CPF e detalhes de doações por ID. "
                "Responda sempre em português do Brasil e de maneira amigável."
            ),
            llm=self.llm,
            tools=[HemoesGetDoadorTool(), HemoesGetDoacaoTool()],
            verbose=True,
            allow_delegation=False
        )

    def create_detran_agent(self) -> Agent:
        """Cria agente para DETRAN."""
        return Agent(
            role='Assistente Virtual do DETRAN-ES',
            goal='Fornecer informações sobre veículos e perfis de cidadãos, sempre em português.',
            backstory=(
                "Você é um assistente virtual especializado nos serviços do DETRAN do Espírito Santo. "
                "Você utiliza ferramentas para consultar veículos, perfis de usuários e atualizar dados. "
                "Sua comunicação deve ser clara, objetiva e estritamente em português do Brasil."
            ),
            llm=self.llm,
            tools=[
                DetranSearchVehiclesTool(),
                DetranFetchProfileTool(),
                DetranAtualizarVeiculosTool()
            ],
            verbose=True,
            allow_delegation=False
        )

    def create_sesa_agent(self) -> Agent:
        """Cria agente para SESA."""
        return Agent(
            role='Assistente Virtual de Saúde Pública',
            goal='Ajudar usuários a encontrar informações e a gerenciar agendamentos de saúde na SESA, respondendo em português.',
            backstory=(
                "Você é um assistente virtual da Secretaria de Saúde (SESA), projetado para facilitar o acesso aos serviços. "
                "Você pode listar municípios e serviços, encontrar unidades, verificar horários, obter sugestões, e ajudar a realizar ou cancelar agendamentos. "
                "Seja sempre prestativo e responda em português do Brasil."
            ),
            llm=self.llm,
            tools=[
                SesaGetMunicipiosTool(),
                SesaGetServicosTool(),
                SesaGetUnidadesTool(),
                SesaGetHorariosTool(),
                SesaGetSugestaoAgendamentoTool(),
                SesaReservarHorarioTool(),
                SesaCheckAgendamentoExistenteTool(),
                SesaCancelarAgendamentoTool()
            ],
            verbose=True,
            allow_delegation=False
        )

    def create_all_agents(self) -> Dict[str, Agent]:
        """Cria todos os agentes."""
        return {
            'hemoes': self.create_hemoes_agent(),
            'detran': self.create_detran_agent(),
            'sesa': self.create_sesa_agent()
        }