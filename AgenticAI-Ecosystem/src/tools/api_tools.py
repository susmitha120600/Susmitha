from typing import Dict, Any, Optional, List
import httpx
import asyncio
from langchain.tools import Tool
from src.core.logging import get_logger
from src.core.exceptions import ToolExecutionError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class APITools:
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self.session is None:
            self.session = httpx.AsyncClient(timeout=self.timeout)
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.aclose()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        session = await self._get_session()
        
        try:
            response = await session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data
            )
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except:
                result = {"text": response.text}
            
            logger.info(f"API request successful: {method} {url} (status={response.status_code})")
            
            return {
                'success': True,
                'status_code': response.status_code,
                'data': result,
                'headers': dict(response.headers)
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {str(e)}")
            raise ToolExecutionError(
                f"API request failed with status {e.response.status_code}",
                details={
                    "url": url,
                    "status_code": e.response.status_code,
                    "error": str(e)
                }
            )
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            raise ToolExecutionError(
                "API request failed",
                details={"url": url, "error": str(e)}
            )
    
    def make_request_sync(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.make_request(method, url, headers, params, json_data, data)
        )
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        url = f"https://api.weatherapi.com/v1/current.json"
        params = {
            "q": location,
            "key": "demo"
        }
        
        try:
            result = self.make_request_sync("GET", url, params=params)
            return result['data']
        except Exception as e:
            logger.warning(f"Weather API call failed: {str(e)}")
            return {"error": str(e)}
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        logger.info(f"Web search requested: {query}")
        
        return [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a sample search result snippet for query: {query}"
            }
            for i in range(num_results)
        ]
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        logger.info(f"Stock price requested: {symbol}")
        
        return {
            "symbol": symbol,
            "price": 150.25,
            "change": 2.5,
            "change_percent": 1.69,
            "note": "This is demo data. Integrate with real API like Alpha Vantage or Yahoo Finance."
        }
    
    def get_news(self, topic: str, limit: int = 5) -> List[Dict[str, str]]:
        logger.info(f"News requested: {topic}")
        
        return [
            {
                "title": f"News article {i+1} about {topic}",
                "source": "Demo News Source",
                "url": f"https://news.example.com/article{i+1}",
                "published_at": "2024-01-01T12:00:00Z",
                "summary": f"This is a sample news summary about {topic}"
            }
            for i in range(limit)
        ]
    
    def get_langchain_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_weather",
                func=self.get_weather,
                description="Get current weather information for a location. "
                           "Input should be a city name or location string."
            ),
            Tool(
                name="search_web",
                func=lambda q: str(self.search_web(q)),
                description="Search the web for information. "
                           "Input should be a search query string."
            ),
            Tool(
                name="get_stock_price",
                func=lambda s: str(self.get_stock_price(s)),
                description="Get current stock price for a symbol. "
                           "Input should be a stock ticker symbol (e.g., AAPL, GOOGL)."
            ),
            Tool(
                name="get_news",
                func=lambda t: str(self.get_news(t)),
                description="Get recent news articles about a topic. "
                           "Input should be a topic or keyword string."
            ),
            Tool(
                name="api_request",
                func=lambda args: str(self._parse_and_execute_api_request(args)),
                description="Make a custom API request. Input should be a JSON string with "
                           "keys: method, url, and optionally headers, params, json_data. "
                           "Example: {\"method\": \"GET\", \"url\": \"https://api.example.com/data\"}"
            )
        ]
    
    def _parse_and_execute_api_request(self, args: str) -> Dict[str, Any]:
        import json
        
        try:
            request_data = json.loads(args)
            method = request_data.get('method', 'GET')
            url = request_data['url']
            headers = request_data.get('headers')
            params = request_data.get('params')
            json_data = request_data.get('json_data')
            
            return self.make_request_sync(method, url, headers, params, json_data)
            
        except Exception as e:
            logger.error(f"Error parsing API request: {str(e)}")
            return {"error": str(e)}
