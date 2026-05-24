from app.services.ingestion import DocumentChunk, load_document_catalog


DOCUMENT_CATALOG: tuple[DocumentChunk, ...] = load_document_catalog()
