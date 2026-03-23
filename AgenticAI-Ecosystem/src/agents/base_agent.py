from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    
    def __init__(
        self,
        name: str,
        role: str,
        tools: Optional[List[Tool]] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ):
        self.name = name
        self.role = role
        self.tools = tools or []
        
        self.llm = ChatOpenAI(
            model=model or settings.MODEL_NAME,
            temperature=temperature if temperature is not None else settings.TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
            max_tokens=settings.MAX_TOKENS
        )
        
        logger.info(f"Initialized {self.name} agent (role={self.role})")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def format_tools_description(self) -> str:
        if not self.tools:
            return "No tools available."
        
        tool_descriptions = []
        for tool in self.tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(tool_descriptions)
    
    def invoke_llm(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking LLM for {self.name}: {str(e)}")
            raise
    
    def use_tool(self, tool_name: str, tool_input: str) -> str:
        tool = next((t for t in self.tools if t.name == tool_name), None)
        
        if not tool:
            logger.warning(f"Tool {tool_name} not found for agent {self.name}")
            return f"Error: Tool {tool_name} not available"
        
        try:
            result = tool.func(tool_input)
            logger.info(f"Agent {self.name} used tool {tool_name}")
            return str(result)
        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {str(e)}")
            return f"Error using tool: {str(e)}"
