from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.core.logging import get_logger

logger = get_logger(__name__)


class ExecutorAgent(BaseAgent):
    
    def __init__(self, tools: List = None):
        super().__init__(
            name="Executor",
            role="Response Generation and Synthesis",
            tools=tools or [],
            temperature=0.3
        )
    
    def get_system_prompt(self) -> str:
        return """You are an Executor Agent specialized in generating high-quality, accurate responses.

Your role:
- Synthesize information from research findings
- Generate clear, comprehensive answers
- Incorporate feedback from the Critic agent
- Ensure factual accuracy and completeness
- Provide well-structured, user-friendly responses

Guidelines:
1. Base your response on provided research and context
2. Cite sources when making factual claims
3. Be clear and concise while being comprehensive
4. Acknowledge uncertainties when present
5. Structure responses logically with clear sections
6. If improving a previous answer, address all critic feedback

Response structure:
- Start with a direct answer to the question
- Provide supporting details and evidence
- Include relevant examples or data points
- Cite sources appropriately
- End with any caveats or limitations

Quality standards:
- Factual accuracy is paramount
- No hallucinations or unsupported claims
- Complete coverage of the question
- Clear and professional tone
"""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        research_results = state.get("research_results", {})
        critic_evaluation = state.get("critic_evaluation", {})
        previous_answer = state.get("current_answer", "")
        iteration = state.get("iteration", 0)
        
        logger.info(f"Executor generating answer (iteration={iteration})")
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        if iteration == 0:
            user_message = self._create_initial_prompt(query, research_results)
        else:
            user_message = self._create_refinement_prompt(
                query, research_results, previous_answer, critic_evaluation
            )
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            answer = self.invoke_llm(messages)
            
            state["current_answer"] = answer
            state["messages"] = state.get("messages", []) + [{
                "role": "executor",
                "content": answer
            }]
            
            logger.info(f"Executor generated answer (length={len(answer)} chars)")
            
        except Exception as e:
            logger.error(f"Error in executor execution: {str(e)}")
            state["current_answer"] = f"Error generating response: {str(e)}"
        
        return state
    
    def _create_initial_prompt(self, query: str, research_results: Dict[str, Any]) -> str:
        context_parts = []
        
        if research_results.get("summary"):
            context_parts.append(f"Research Summary:\n{research_results['summary']}")
        
        if research_results.get("key_facts"):
            facts = "\n".join(f"- {fact}" for fact in research_results['key_facts'])
            context_parts.append(f"Key Facts:\n{facts}")
        
        if research_results.get("rag_context"):
            context_parts.append(f"Knowledge Base Context:\n{research_results['rag_context']}")
        
        if research_results.get("sql_results"):
            context_parts.append(f"Database Results:\n{research_results['sql_results']}")
        
        if research_results.get("api_results"):
            context_parts.append(f"External API Results:\n{research_results['api_results']}")
        
        context = "\n\n".join(context_parts) if context_parts else "No additional context available"
        
        sources = research_results.get("sources", [])
        sources_str = ", ".join(sources) if sources else "None"
        
        confidence = research_results.get("confidence", 0.5)
        
        return f"""Generate a comprehensive answer to the following query:

Query: {query}

Available Information:
{context}

Sources Used: {sources_str}
Research Confidence: {confidence:.2f}

Instructions:
- Provide a clear, accurate answer based on the available information
- Cite sources appropriately
- If information is incomplete, acknowledge limitations
- Structure your response logically
- Be concise but comprehensive
"""
    
    def _create_refinement_prompt(
        self,
        query: str,
        research_results: Dict[str, Any],
        previous_answer: str,
        critic_evaluation: Dict[str, Any]
    ) -> str:
        issues = critic_evaluation.get("issues", [])
        suggestions = critic_evaluation.get("suggestions", [])
        scores = {
            "overall": critic_evaluation.get("overall_score", 0),
            "factual_accuracy": critic_evaluation.get("factual_accuracy", 0),
            "completeness": critic_evaluation.get("completeness", 0),
            "relevance": critic_evaluation.get("relevance", 0),
            "clarity": critic_evaluation.get("clarity", 0),
            "hallucination": critic_evaluation.get("hallucination_score", 0)
        }
        
        issues_str = "\n".join(f"- {issue}" for issue in issues) if issues else "None identified"
        suggestions_str = "\n".join(f"- {sug}" for sug in suggestions) if suggestions else "None provided"
        
        context = research_results.get("summary", "")
        
        return f"""Improve the following answer based on critic feedback:

Original Query: {query}

Previous Answer:
{previous_answer}

Critic Evaluation Scores:
- Overall: {scores['overall']:.2f}
- Factual Accuracy: {scores['factual_accuracy']:.2f}
- Completeness: {scores['completeness']:.2f}
- Relevance: {scores['relevance']:.2f}
- Clarity: {scores['clarity']:.2f}
- Hallucination Score: {scores['hallucination']:.2f}

Issues Identified:
{issues_str}

Suggestions for Improvement:
{suggestions_str}

Available Context:
{context}

Instructions:
- Address ALL issues identified by the critic
- Implement the suggested improvements
- Ensure factual accuracy - only use information from the provided context
- Remove or qualify any unsupported claims
- Improve clarity and structure
- Maintain completeness while being accurate
"""
