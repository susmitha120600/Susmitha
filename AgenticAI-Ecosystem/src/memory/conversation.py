from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_openai import ChatOpenAI
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    
    def __init__(
        self,
        session_id: str,
        memory_type: str = "buffer",
        max_token_limit: int = 2000
    ):
        self.session_id = session_id
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit
        self.conversation_history: List[Dict[str, Any]] = []
        
        if memory_type == "buffer":
            self.memory = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
        elif memory_type == "summary":
            llm = ChatOpenAI(
                model=settings.MODEL_NAME,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )
            self.memory = ConversationSummaryMemory(
                llm=llm,
                return_messages=True,
                memory_key="chat_history"
            )
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")
        
        logger.info(f"Initialized conversation memory: session={session_id}, type={memory_type}")
    
    def add_user_message(self, message: str):
        self.memory.chat_memory.add_user_message(message)
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.debug(f"Added user message to memory (session={self.session_id})")
    
    def add_ai_message(self, message: str):
        self.memory.chat_memory.add_ai_message(message)
        self.conversation_history.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.debug(f"Added AI message to memory (session={self.session_id})")
    
    def add_system_message(self, message: str):
        self.conversation_history.append({
            "role": "system",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_memory_variables(self) -> Dict[str, Any]:
        return self.memory.load_memory_variables({})
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history
    
    def clear(self):
        self.memory.clear()
        self.conversation_history = []
        logger.info(f"Cleared conversation memory (session={self.session_id})")
    
    def get_context_string(self, max_messages: Optional[int] = None) -> str:
        history = self.conversation_history
        if max_messages:
            history = history[-max_messages:]
        
        context_lines = []
        for msg in history:
            role = msg['role'].capitalize()
            content = msg['content']
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump({
                'session_id': self.session_id,
                'memory_type': self.memory_type,
                'conversation_history': self.conversation_history
            }, f, indent=2)
        logger.info(f"Saved conversation memory to {filepath}")
    
    def load_from_file(self, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.session_id = data['session_id']
        self.memory_type = data['memory_type']
        self.conversation_history = data['conversation_history']
        
        for msg in self.conversation_history:
            if msg['role'] == 'user':
                self.memory.chat_memory.add_user_message(msg['content'])
            elif msg['role'] == 'assistant':
                self.memory.chat_memory.add_ai_message(msg['content'])
        
        logger.info(f"Loaded conversation memory from {filepath}")
