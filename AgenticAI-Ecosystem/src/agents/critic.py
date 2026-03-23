from typing import Dict, Any, List
import json
from .base_agent import BaseAgent
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class CriticAgent(BaseAgent):
    
    def __init__(self, tools: List = None):
        super().__init__(
            name="Critic",
            role="Quality Assurance and Validation",
            tools=tools or [],
            temperature=0.0
        )
        self.hallucination_threshold = settings.HALLUCINATION_THRESHOLD
        self.quality_threshold = settings.QUALITY_THRESHOLD
    
    def get_system_prompt(self) -> str:
        return f"""You are a Critic Agent specialized in validating AI outputs for quality and accuracy.

Your role:
- Evaluate factual accuracy of responses
- Detect hallucinations and unsupported claims
- Assess answer completeness and relevance
- Verify consistency with source material
- Provide actionable feedback for improvement

Evaluation criteria:
1. Factual Accuracy (0-1): Are all claims supported by evidence?
2. Completeness (0-1): Does it fully answer the question?
3. Relevance (0-1): Is the response on-topic?
4. Clarity (0-1): Is it well-structured and understandable?
5. Source Alignment (0-1): Does it align with provided context?

Hallucination detection:
- Flag unsupported claims
- Identify contradictions with source material
- Note speculative statements presented as facts
- Check for fabricated details

Quality threshold: {self.quality_threshold}
Hallucination threshold: {self.hallucination_threshold}

Provide your evaluation as JSON with:
- overall_score: float (0-1)
- factual_accuracy: float (0-1)
- completeness: float (0-1)
- relevance: float (0-1)
- clarity: float (0-1)
- source_alignment: float (0-1)
- hallucination_score: float (0-1, higher = more hallucination)
- issues: list of specific problems found
- suggestions: list of improvement recommendations
- approved: boolean (true if meets quality threshold)
"""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        answer = state.get("current_answer", "")
        research_results = state.get("research_results", {})
        iteration = state.get("iteration", 0)
        
        logger.info(f"Critic evaluating answer (iteration={iteration})")
        
        context_info = self._format_context(research_results)
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Evaluate the following response:

Query: {query}

Answer to evaluate:
{answer}

Available context and research:
{context_info}

Provide a detailed evaluation following the JSON format specified in your system prompt.
"""}
        ]
        
        try:
            response = self.invoke_llm(messages)
            
            evaluation = self._parse_evaluation(response)
            
            state["critic_evaluation"] = evaluation
            state["messages"] = state.get("messages", []) + [{
                "role": "critic",
                "content": f"Evaluation: Score={evaluation['overall_score']:.2f}, "
                          f"Hallucination={evaluation['hallucination_score']:.2f}, "
                          f"Approved={evaluation['approved']}"
            }]
            
            logger.info(
                f"Critic evaluation: score={evaluation['overall_score']:.2f}, "
                f"hallucination={evaluation['hallucination_score']:.2f}, "
                f"approved={evaluation['approved']}"
            )
            
        except Exception as e:
            logger.error(f"Error in critic execution: {str(e)}")
            state["critic_evaluation"] = {
                "overall_score": 0.5,
                "approved": False,
                "issues": [f"Evaluation error: {str(e)}"],
                "suggestions": ["Retry evaluation"]
            }
        
        return state
    
    def _format_context(self, research_results: Dict[str, Any]) -> str:
        context_parts = []
        
        if research_results.get("rag_context"):
            context_parts.append(f"RAG Context:\n{research_results['rag_context']}")
        
        if research_results.get("sql_results"):
            context_parts.append(f"SQL Results:\n{research_results['sql_results']}")
        
        if research_results.get("api_results"):
            context_parts.append(f"API Results:\n{research_results['api_results']}")
        
        if research_results.get("summary"):
            context_parts.append(f"Research Summary:\n{research_results['summary']}")
        
        return "\n\n".join(context_parts) if context_parts else "No context available"
    
    def _parse_evaluation(self, response: str) -> Dict[str, Any]:
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(response)
            
            evaluation.setdefault("overall_score", 0.5)
            evaluation.setdefault("factual_accuracy", 0.5)
            evaluation.setdefault("completeness", 0.5)
            evaluation.setdefault("relevance", 0.5)
            evaluation.setdefault("clarity", 0.5)
            evaluation.setdefault("source_alignment", 0.5)
            evaluation.setdefault("hallucination_score", 0.5)
            evaluation.setdefault("issues", [])
            evaluation.setdefault("suggestions", [])
            
            evaluation["approved"] = (
                evaluation["overall_score"] >= self.quality_threshold and
                evaluation["hallucination_score"] <= self.hallucination_threshold
            )
            
            return evaluation
            
        except Exception as e:
            logger.warning(f"Failed to parse evaluation JSON: {str(e)}")
            return {
                "overall_score": 0.5,
                "factual_accuracy": 0.5,
                "completeness": 0.5,
                "relevance": 0.5,
                "clarity": 0.5,
                "source_alignment": 0.5,
                "hallucination_score": 0.5,
                "issues": ["Failed to parse evaluation"],
                "suggestions": [],
                "approved": False
            }
