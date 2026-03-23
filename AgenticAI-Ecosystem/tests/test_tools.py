import pytest
from unittest.mock import Mock, patch, MagicMock
from src.tools import APITools


class TestAPITools:
    
    @pytest.fixture
    def api_tools(self):
        return APITools(timeout=10)
    
    def test_initialization(self, api_tools):
        assert api_tools.timeout == 10
        assert api_tools.session is None
    
    def test_get_weather(self, api_tools):
        result = api_tools.get_weather("London")
        assert isinstance(result, dict)
    
    def test_search_web(self, api_tools):
        results = api_tools.search_web("test query", num_results=3)
        assert len(results) == 3
        assert all('title' in r for r in results)
        assert all('url' in r for r in results)
    
    def test_get_stock_price(self, api_tools):
        result = api_tools.get_stock_price("AAPL")
        assert isinstance(result, dict)
        assert 'symbol' in result
        assert 'price' in result
    
    def test_get_news(self, api_tools):
        results = api_tools.get_news("technology", limit=5)
        assert len(results) == 5
        assert all('title' in r for r in results)
    
    def test_get_langchain_tools(self, api_tools):
        tools = api_tools.get_langchain_tools()
        assert len(tools) > 0
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)


class TestSQLTools:
    
    @pytest.fixture
    def mock_engine(self):
        with patch('src.tools.sql_tools.create_engine') as mock:
            yield mock
    
    def test_format_schema_for_prompt(self, mock_engine):
        from src.tools.sql_tools import SQLTools
        
        with patch.object(SQLTools, '__init__', lambda x, y=None: None):
            sql_tools = SQLTools.__new__(SQLTools)
            
            schema_info = {
                'users': {
                    'columns': [
                        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
                        {'name': 'name', 'type': 'VARCHAR', 'nullable': True}
                    ],
                    'primary_keys': ['id']
                }
            }
            
            result = sql_tools._format_schema_for_prompt(schema_info)
            
            assert 'users' in result
            assert 'id' in result
            assert 'name' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
