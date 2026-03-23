import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from src.graph import AgenticWorkflow
from src.tools import APITools
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main():
    logger.info("Starting basic query example")
    
    api_tools = APITools()
    
    workflow = AgenticWorkflow(
        retriever=None,
        reranker=None,
        sql_tools=None,
        api_tools=api_tools
    )
    
    query = "What is the weather like in San Francisco?"
    
    logger.info(f"Processing query: {query}")
    
    result = await workflow.arun(
        query=query,
        use_rag=False,
        use_sql=False,
        use_api=True,
        enable_self_correction=True,
        max_iterations=2
    )
    
    print("\n" + "="*80)
    print("QUERY RESULT")
    print("="*80)
    print(f"\nQuery: {query}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nMetadata:")
    print(f"  - Iterations: {result['iterations']}")
    print(f"  - Final Score: {result['metadata']['final_score']:.2f}")
    print(f"  - Hallucination Score: {result['metadata']['hallucination_score']:.2f}")
    print(f"  - Approved: {result['metadata']['approved']}")
    print(f"  - Sources: {', '.join(result['metadata']['sources'])}")
    print("="*80 + "\n")
    
    await api_tools.close()


if __name__ == "__main__":
    asyncio.run(main())
