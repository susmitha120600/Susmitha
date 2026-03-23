import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.graph import AgenticWorkflow
from src.rag import DocumentIngestion, TextChunker, HybridRetriever, CrossEncoderReranker
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main():
    logger.info("Starting RAG example")
    
    logger.info("Step 1: Ingesting sample documents")
    ingestion = DocumentIngestion()
    
    sample_docs = [
        "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France. It is named after the engineer Gustave Eiffel, whose company designed and built the tower. Constructed from 1887 to 1889, it was initially criticized by some of France's leading artists and intellectuals for its design, but it has become a global cultural icon of France and one of the most recognizable structures in the world.",
        
        "Python is a high-level, interpreted programming language with dynamic semantics. Its high-level built-in data structures, combined with dynamic typing and dynamic binding, make it very attractive for Rapid Application Development, as well as for use as a scripting or glue language to connect existing components together.",
        
        "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention. Machine learning algorithms are used in a wide variety of applications, such as in medicine, email filtering, speech recognition, and computer vision.",
        
        "The Amazon rainforest, also known as Amazonia, is a moist broadleaf tropical rainforest in the Amazon biome that covers most of the Amazon basin of South America. This basin encompasses 7,000,000 km2, of which 5,500,000 km2 are covered by the rainforest. The majority of the forest is contained within Brazil, with 60% of the rainforest, followed by Peru with 13%, and Colombia with 10%."
    ]
    
    for i, text in enumerate(sample_docs):
        ingestion.load_from_text(text, metadata={"source": f"sample_doc_{i+1}", "topic": ["geography", "technology", "AI", "nature"][i]})
    
    logger.info(f"Loaded {len(sample_docs)} documents")
    
    logger.info("Step 2: Chunking documents")
    chunker = TextChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk_documents(ingestion.get_documents())
    logger.info(f"Created {len(chunks)} chunks")
    
    logger.info("Step 3: Building vector index")
    retriever = HybridRetriever()
    retriever.build_index(chunks)
    retriever.save_index()
    logger.info("Vector index built and saved")
    
    logger.info("Step 4: Initializing reranker")
    reranker = CrossEncoderReranker()
    
    logger.info("Step 5: Creating workflow")
    workflow = AgenticWorkflow(
        retriever=retriever,
        reranker=reranker,
        sql_tools=None,
        api_tools=None
    )
    
    queries = [
        "Tell me about the Eiffel Tower",
        "What is machine learning?",
        "Describe the Amazon rainforest"
    ]
    
    for query in queries:
        logger.info(f"\nProcessing query: {query}")
        
        result = await workflow.arun(
            query=query,
            use_rag=True,
            use_sql=False,
            use_api=False,
            enable_self_correction=True,
            max_iterations=3
        )
        
        print("\n" + "="*80)
        print(f"Query: {query}")
        print("="*80)
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nMetadata:")
        print(f"  - Iterations: {result['iterations']}")
        print(f"  - Final Score: {result['metadata']['final_score']:.2f}")
        print(f"  - Confidence: {result['metadata']['confidence']:.2f}")
        print(f"  - Hallucination Score: {result['metadata']['hallucination_score']:.2f}")
        print(f"  - Approved: {result['metadata']['approved']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
