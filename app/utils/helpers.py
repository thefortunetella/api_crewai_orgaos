import json
import logging
from typing import Any, Dict, Optional
from crewai import Agent, Task, Crew

logger = logging.getLogger(__name__)

def json_dumps(data: Any) -> str:
    """Serializa dados para JSON com formatação."""
    return json.dumps(data, indent=2)

def process_query(agent: Agent, query: str, orgao: str, 
                 user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Processa uma consulta usando um agente CrewAI."""
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
        return {
            "success": False,
            "error": "Ocorreu um erro interno ao processar sua solicitação."
        }