import logging
from core.document_loader import load_documents_into_database, DEFAULT_EMBEDDING_MODEL

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    logger.info("Starting baseline indexing using upstream path on 'corpus' directory...")
    # By passing reload=True, it will drop any existing table and re-index
    table = load_documents_into_database(
        model_name=DEFAULT_EMBEDDING_MODEL,
        documents_path="corpus",
        reload=True
    )
    
    # We can check how many rows are in the table
    logger.info(f"Baseline indexing complete. Table has {len(table.to_pandas())} rows.")

if __name__ == "__main__":
    main()
