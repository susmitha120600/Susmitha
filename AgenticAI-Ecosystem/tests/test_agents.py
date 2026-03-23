import pytest
from unittest.mock import Mock, patch
from src.agents import ResearcherAgent, CriticAgent, ExecutorAgent


class TestResearcherAgent:
    
    @pytest.fixture
    def researcher(self):
        return ResearcherAgent(tools=[])
    
    def test_initialization(self, researcher):
        assert researcher.name == "Researcher"
        assert researcher.role == "Information Gathering and Context Retrieval"
        assert researcher.tools == []
    
    def test_get_system_prompt(self, researcher):
        prompt = researcher.get_system_prompt()
        assert "Researcher Agent" in prompt
        assert "retrieve relevant context" in prompt.lower()
    
    @patch('src.agents.researcher.ResearcherAgent.invoke_llm')
    def test_execute(self, mock_llm, researcher):
        mock_llm.return_value = '{"summary": "Test summary", "confidence": 0.8, "key_facts": [], "gaps": []}'
        
        state = {
            "query": "Test query",
            "use_rag": False,
            "use_sql": False,
            "use_api": False,
            "messages": []
        }
        
        result = researcher.execute(state)
        
        assert "research_results" in result
        assert result["research_results"]["summary"] == "Test summary"
        assert result["research_results"]["confidence"] == 0.8


class TestCriticAgent:
    
    @pytest.fixture
    def critic(self):
        return CriticAgent(tools=[])
    
    def test_initialization(self, critic):
        assert critic.name == "Critic"
        assert critic.role == "Quality Assurance and Validation"
    
    def test_get_system_prompt(self, critic):
        prompt = critic.get_system_prompt()
        assert "Critic Agent" in prompt
        assert "hallucination" in prompt.lower()
        assert "quality" in prompt.lower()
    
    @patch('src.agents.critic.CriticAgent.invoke_llm')
    def test_execute(self, mock_llm, critic):
        mock_response = '''{
            "overall_score": 0.9,
            "factual_accuracy": 0.95,
            "completeness": 0.85,
            "relevance": 0.9,
            "clarity": 0.88,
            "source_alignment": 0.92,
            "hallucination_score": 0.05,
            "issues": [],
            "suggestions": [],
            "approved": true
        }'''
        mock_llm.return_value = mock_response
        
        state = {
            "query": "Test query",
            "current_answer": "Test answer",
            "research_results": {},
            "iteration": 0,
            "messages": []
        }
        
        result = critic.execute(state)
        
        assert "critic_evaluation" in result
        assert result["critic_evaluation"]["overall_score"] == 0.9
        assert result["critic_evaluation"]["approved"] == True


class TestExecutorAgent:
    
    @pytest.fixture
    def executor(self):
        return ExecutorAgent(tools=[])
    
    def test_initialization(self, executor):
        assert executor.name == "Executor"
        assert executor.role == "Response Generation and Synthesis"
    
    def test_get_system_prompt(self, executor):
        prompt = executor.get_system_prompt()
        assert "Executor Agent" in prompt
        assert "synthesize" in prompt.lower()
    
    @patch('src.agents.executor.ExecutorAgent.invoke_llm')
    def test_execute_initial(self, mock_llm, executor):
        mock_llm.return_value = "This is a test answer"
        
        state = {
            "query": "Test query",
            "research_results": {"summary": "Test research"},
            "iteration": 0,
            "messages": []
        }
        
        result = executor.execute(state)
        
        assert "current_answer" in result
        assert result["current_answer"] == "This is a test answer"
    
    @patch('src.agents.executor.ExecutorAgent.invoke_llm')
    def test_execute_refinement(self, mock_llm, executor):
        mock_llm.return_value = "This is an improved answer"
        
        state = {
            "query": "Test query",
            "research_results": {"summary": "Test research"},
            "current_answer": "Previous answer",
            "critic_evaluation": {
                "overall_score": 0.6,
                "issues": ["Issue 1"],
                "suggestions": ["Suggestion 1"]
            },
            "iteration": 1,
            "messages": []
        }
        
        result = executor.execute(state)
        
        assert result["current_answer"] == "This is an improved answer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
