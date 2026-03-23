from typing import Dict, Any, List
import json
from .base_agent import BaseAgent
from src.core.logging import get_logger

logger = get_logger(__name__)


class ResearcherAgent(BaseAgent):
    
    def __init__(self, tools: List = None):
        super().__init__(
            name="Researcher",
            role="Information Gathering and Context Retrieval",
            tools=tools or [],
            temperature=0.1
        )
    
    def get_system_prompt(self) -> str:
        return f"""You are a Researcher Agent specialized in gathering comprehensive and accurate information.

Your role:
- Retrieve relevant context from knowledge bases using RAG
- Query SQL databases for structured data
- Call external APIs for real-time information
- Synthesize information from multiple sources
- Provide well-organized, factual research results

Available tools:
{self.format_tools_description()}

Guidelines:
1. Always verify information from multiple sources when possible
2. Prioritize recent and authoritative sources
3. Clearly cite sources in your research
4. Flag any uncertainties or conflicting information
5. Organize findings in a structured format

When you gather information, structure your response as:
- Summary: Brief overview of findings
- Key Facts: Bullet points of important information
- Sources: List of sources used
- Confidence: Your confidence level in the findings (0-1)
- Gaps: Any information gaps or uncertainties
"""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        use_rag = state.get("use_rag", True)
        use_sql = state.get("use_sql", False)
        use_api = state.get("use_api", False)
        
        logger.info(f"Researcher executing: query='{query}', rag={use_rag}, sql={use_sql}, api={use_api}")
        
        research_results = {
            "rag_context": None,
            "sql_results": None,
            "api_results": None,
            "summary": "",
            "sources": [],
            "confidence": 0.0
        }
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Research the following query: {query}"}
        ]
        
        if use_rag and self._has_tool("retrieve_context"):
            try:
                rag_context = self.use_tool("retrieve_context", query)
                research_results["rag_context"] = rag_context
                research_results["sources"].append("Knowledge Base (RAG)")
                messages.append({
                    "role": "assistant",
                    "content": f"Retrieved context from knowledge base:\n{rag_context}"
                })
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {str(e)}")
        
        if use_sql and self._has_tool("query_database"):
            try:
                sql_results = self.use_tool("query_database", query)
                research_results["sql_results"] = sql_results
                research_results["sources"].append("SQL Database")
                messages.append({
                    "role": "assistant",
                    "content": f"Retrieved data from database:\n{sql_results}"
                })
            except Exception as e:
                logger.warning(f"SQL query failed: {str(e)}")
        
        if use_api and self._has_tool("search_web"):
            try:
                api_results = self.use_tool("search_web", query)
                research_results["api_results"] = api_results
                research_results["sources"].append("Web Search API")
                messages.append({
                    "role": "assistant",
                    "content": f"Retrieved information from web:\n{api_results}"
                })
            except Exception as e:
                logger.warning(f"API call failed: {str(e)}")
        
        messages.append({
            "role": "user",
            "content": "Based on the information gathered, provide a comprehensive research summary. "
                      "Include: summary, key facts, confidence level (0-1), and any gaps in information. "
                      "Format your response as JSON with keys: summary, key_facts (list), confidence (float), gaps (list)."
        })
        
        try:
            response = self.invoke_llm(messages)
            
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                parsed_response = json.loads(response)
                research_results["summary"] = parsed_response.get("summary", response)
                research_results["key_facts"] = parsed_response.get("key_facts", [])
                research_results["confidence"] = float(parsed_response.get("confidence", 0.7))
                research_results["gaps"] = parsed_response.get("gaps", [])
            except:
                research_results["summary"] = response
                research_results["confidence"] = 0.7
        
        except Exception as e:
            logger.error(f"Error in researcher execution: {str(e)}")
            research_results["summary"] = f"Error during research: {str(e)}"
            research_results["confidence"] = 0.0
        
        state["research_results"] = research_results
        state["messages"] = state.get("messages", []) + [{
            "role": "researcher",
            "content": research_results["summary"]
        }]
        
        logger.info(f"Researcher completed: confidence={research_results['confidence']:.2f}")
        
        return state
    
    def _has_tool(self, tool_name: str) -> bool:
        return any(tool.name == tool_name for tool in self.tools)
