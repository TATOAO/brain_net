"""
RAG (Retrieval Augmented Generation) API routes for Brain_Net LLM Service
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List

from app.schemas.rag import RAGRequest, RAGResponse, DocumentSearchRequest, DocumentSearchResponse
from app.services.rag import RAGService
from app.core.dependencies import get_rag_service

router = APIRouter()


@router.post("/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> RAGResponse:
    """Perform RAG query with document retrieval and generation."""
    try:
        response = await rag_service.query(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    rag_service: RAGService = Depends(get_rag_service)
) -> DocumentSearchResponse:
    """Search documents in the knowledge base."""
    try:
        response = await rag_service.search_documents(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "default",
    rag_service: RAGService = Depends(get_rag_service)
) -> dict:
    """Upload and process a document for RAG."""
    try:
        # Validate file type
        allowed_types = [
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not supported"
            )
        
        document_id = await rag_service.upload_document(file, collection_name)
        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "filename": file.filename,
            "collection": collection_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> dict:
    """Delete a document from the knowledge base."""
    try:
        await rag_service.delete_document(document_id)
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")


@router.get("/collections")
async def list_collections(
    rag_service: RAGService = Depends(get_rag_service)
) -> dict:
    """List all document collections."""
    try:
        collections = await rag_service.list_collections()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/collections/{collection_name}/reindex")
async def reindex_collection(
    collection_name: str,
    rag_service: RAGService = Depends(get_rag_service)
) -> dict:
    """Reindex a document collection."""
    try:
        await rag_service.reindex_collection(collection_name)
        return {"message": f"Collection {collection_name} reindexing started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection reindexing failed: {str(e)}") 