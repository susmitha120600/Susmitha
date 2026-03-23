from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from src.agents import ResearcherAgent, CriticAgent, ExecutorAgent
from src.tools import SQLTools, APITools, RAGTools
from src.rag import HybridRetriever, CrossEncoderReranker
from src.core.config import settings
from src.core.logging import get_logger
from .state import AgentState

logger = get_logger(__name__)


class AgenticWorkflow:
    
    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        sql_tools: Optional[SQLTools] = None,
        api_tools: Optional[APITools] = None
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.sql_tools = sql_tools
        self.api_tools = api_tools
        
        self._initialize_tools()
        self._initialize_agents()
        self.workflow = self._build_workflow()
        
        logger.info("Initialized AgenticWorkflow with self-correction loop")
    
    def _initialize_tools(self):
        all_tools = []
        
        if self.retriever:
            rag_tools = RAGTools(self.retriever, self.reranker)
            all_tools.extend(rag_tools.get_langchain_tools())
        
        if self.sql_tools:
            all_tools.extend(self.sql_tools.get_langchain_tools())
        
        if self.api_tools:
            all_tools.extend(self.api_tools.get_langchain_tools())
        
        self.tools = all_tools
        logger.info(f"Initialized {len(self.tools)} tools for agents")
    
    def _initialize_agents(self):
        self.researcher = ResearcherAgent(tools=self.tools)
        self.critic = CriticAgent(tools=[])
        self.executor = ExecutorAgent(tools=[])
        
        logger.info("Initialized all agents (Researcher, Critic, Executor)")
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("finalize", self._finalize_node)
        
        workflow.set_entry_point("researcher")
        
        workflow.add_edge("researcher", "executor")
        
        workflow.add_conditional_edges(
            "executor",
            self._should_critique,
            {
                "critique": "critic",
                "finalize": "finalize"
            }
        )
        
        workflow.add_conditional_edges(
            "critic",
            self._should_continue,
            {
                "continue": "executor",
                "end": "finalize"
            }
        )
        
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _researcher_node(self, state: AgentState) -> AgentState:
        logger.info("Executing Researcher node")
        return self.researcher.execute(state)
    
    def _executor_node(self, state: AgentState) -> AgentState:
        logger.info(f"Executing Executor node (iteration={state['iteration']})")
        return self.executor.execute(state)
    
    def _critic_node(self, state: AgentState) -> AgentState:
        logger.info(f"Executing Critic node (iteration={state['iteration']})")
        state = self.critic.execute(state)
        state["iteration"] += 1
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        logger.info("Finalizing workflow")
        
        state["final_answer"] = state["current_answer"]
        
        evaluation = state.get("critic_evaluation", {})
        research = state.get("research_results", {})
        
        state["metadata"] = {
            "total_iterations": state["iteration"],
            "final_score": evaluation.get("overall_score", 0.0),
            "hallucination_score": evaluation.get("hallucination_score", 0.0),
            "confidence": research.get("confidence", 0.0),
            "sources": research.get("sources", []),
            "approved": evaluation.get("approved", False)
        }
        
        logger.info(
            f"Workflow completed: iterations={state['iteration']}, "
            f"score={state['metadata']['final_score']:.2f}, "
            f"approved={state['metadata']['approved']}"
        )
        
        return state
    
    def _should_critique(self, state: AgentState) -> str:
        if not state.get("enable_self_correction", True):
            return "finalize"
        
        if state["iteration"] >= state["max_iterations"]:
            logger.info("Max iterations reached, skipping critique")
            return "finalize"
        
        return "critique"
    
    def _should_continue(self, state: AgentState) -> str:
        evaluation = state.get("critic_evaluation", {})
        
        approved = evaluation.get("approved", False)
        
        if approved:
            logger.info("Answer approved by critic, ending loop")
            return "end"
        
        if state["iteration"] >= state["max_iterations"]:
            logger.info("Max iterations reached, ending loop")
            return "end"
        
        logger.info(f"Answer not approved, continuing (iteration {state['iteration']}/{state['max_iterations']})")
        return "continue"
    
    def run(
        self,
        query: str,
        use_rag: bool = True,
        use_sql: bool = False,
        use_api: bool = False,
        enable_self_correction: bool = True,
        max_iterations: Optional[int] = None,
        quality_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        initial_state: AgentState = {
            "query": query,
            "current_answer": "",
            "research_results": {},
            "critic_evaluation": {},
            "iteration": 0,
            "max_iterations": max_iterations or settings.MAX_ITERATIONS,
            "messages": [],
            "use_rag": use_rag,
            "use_sql": use_sql,
            "use_api": use_api,
            "enable_self_correction": enable_self_correction,
            "quality_threshold": quality_threshold or settings.QUALITY_THRESHOLD,
            "final_answer": None,
            "metadata": {}
        }
        
        logger.info(
            f"Starting workflow: query='{query[:50]}...', "
            f"rag={use_rag}, sql={use_sql}, api={use_api}, "
            f"self_correction={enable_self_correction}"
        )
        
        try:
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "answer": final_state["final_answer"],
                "metadata": final_state["metadata"],
                "iterations": final_state["iteration"],
                "messages": final_state["messages"],
                "research_results": final_state["research_results"],
                "critic_evaluation": final_state.get("critic_evaluation", {})
            }
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            raise
    
    async def arun(
        self,
        query: str,
        use_rag: bool = True,
        use_sql: bool = False,
        use_api: bool = False,
        enable_self_correction: bool = True,
        max_iterations: Optional[int] = None,
        quality_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        initial_state: AgentState = {
            "query": query,
            "current_answer": "",
            "research_results": {},
            "critic_evaluation": {},
            "iteration": 0,
            "max_iterations": max_iterations or settings.MAX_ITERATIONS,
            "messages": [],
            "use_rag": use_rag,
            "use_sql": use_sql,
            "use_api": use_api,
            "enable_self_correction": enable_self_correction,
            "quality_threshold": quality_threshold or settings.QUALITY_THRESHOLD,
            "final_answer": None,
            "metadata": {}
        }
        
        logger.info(
            f"Starting async workflow: query='{query[:50]}...', "
            f"rag={use_rag}, sql={use_sql}, api={use_api}"
        )
        
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            
            return {
                "answer": final_state["final_answer"],
                "metadata": final_state["metadata"],
                "iterations": final_state["iteration"],
                "messages": final_state["messages"],
                "research_results": final_state["research_results"],
                "critic_evaluation": final_state.get("critic_evaluation", {})
            }
            
        except Exception as e:
            logger.error(f"Error in async workflow execution: {str(e)}")
            raise
