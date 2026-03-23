import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import DocumentIngestion, TextChunker, HybridRetriever
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def ingest_documents(path: str, recursive: bool = True):
    logger.info(f"Starting document ingestion from: {path}")
    
    ingestion = DocumentIngestion()
    
    path_obj = Path(path)
    if path_obj.is_file():
        logger.info(f"Ingesting single file: {path}")
        documents = ingestion.load_file(path)
    elif path_obj.is_dir():
        logger.info(f"Ingesting directory: {path} (recursive={recursive})")
        documents = ingestion.load_directory(path, recursive=recursive)
    else:
        raise ValueError(f"Path does not exist: {path}")
    
    logger.info(f"Loaded {len(documents)} documents")
    
    stats = ingestion.get_statistics()
    logger.info(f"Document statistics: {stats}")
    
    chunker = TextChunker()
    chunks = chunker.chunk_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")
    
    retriever = HybridRetriever()
    retriever.build_index(chunks)
    logger.info("Built vector index")
    
    retriever.save_index()
    logger.info("Saved vector index")
    
    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "stats": stats
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the vector database")
    parser.add_argument("--path", type=str, required=True, help="Path to file or directory")
    parser.add_argument("--no-recursive", action="store_true", help="Don't recursively scan directories")
    
    args = parser.parse_args()
    
    try:
        result = ingest_documents(args.path, recursive=not args.no_recursive)
        
        print("\n" + "="*80)
        print("Document Ingestion Complete")
        print("="*80)
        print(f"\nDocuments processed: {result['documents']}")
        print(f"Chunks created: {result['chunks']}")
        print(f"\nStatistics:")
        print(f"  - Total characters: {result['stats']['total_characters']:,}")
        print(f"  - Average length: {result['stats']['average_length']:,}")
        print(f"  - File types: {result['stats']['file_types']}")
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
