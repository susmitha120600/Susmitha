from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator


class AgentState(TypedDict):
    query: str
    current_answer: str
    research_results: Dict[str, Any]
    critic_evaluation: Dict[str, Any]
    iteration: int
    max_iterations: int
    messages: Annotated[List[Dict[str, str]], operator.add]
    use_rag: bool
    use_sql: bool
    use_api: bool
    enable_self_correction: bool
    quality_threshold: float
    final_answer: Optional[str]
    metadata: Dict[str, Any]
