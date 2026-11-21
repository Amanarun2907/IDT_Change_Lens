import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all ChangeLens AI Specialists.
    Enforces structured roles, instructions, inputs, outputs, and resilient execution.
    """
    def __init__(self, name: str, role: str, llm_service: Optional[LLMService] = None):
        self.name = name
        self.role = role
        self.llm = llm_service or LLMService()

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's specialist task with shared state.
        Returns a dict of updates to merge into the shared state.
        """
        pass
