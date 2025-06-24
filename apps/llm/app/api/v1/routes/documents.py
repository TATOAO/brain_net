"""
Document processing API routes for Brain_Net LLM Service
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List

from app.schemas.documents import (
    DocumentProcessRequest, DocumentProcessResponse,
    DocumentMetadata, DocumentChunk, EmbeddingRequest, EmbeddingResponse
)
from app.services.documents import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter()


@router.post("/process", response_model=DocumentProcessResponse)
async def process_document(
    file: UploadFile = File(...),
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentProcessResponse:
    """Process a document and extract text chunks."""
    try:
        response = await document_service.process_document(
            file, chunk_size, chunk_overlap
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    document_service: DocumentService = Depends(get_document_service)
) -> EmbeddingResponse:
    """Generate embeddings for text chunks."""
    try:
        response = await document_service.generate_embeddings(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.get("/metadata/{document_id}", response_model=DocumentMetadata)
async def get_document_metadata(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentMetadata:
    """Get metadata for a document."""
    try:
        metadata = await document_service.get_document_metadata(document_id)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document metadata: {str(e)}")


@router.get("/chunks/{document_id}")
async def get_document_chunks(
    document_id: str,
    limit: int = 100,
    offset: int = 0,
    document_service: DocumentService = Depends(get_document_service)
) -> List[DocumentChunk]:
    """Get chunks for a document."""
    try:
        chunks = await document_service.get_document_chunks(document_id, limit, offset)
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document chunks: {str(e)}")


@router.post("/extract-text")
async def extract_text(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
) -> dict:
    """Extract raw text from a document."""
    try:
        text = await document_service.extract_text(file)
        return {
            "filename": file.filename,
            "text": text,
            "length": len(text)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
) -> dict:
    """Analyze document structure and content."""
    try:
        analysis = await document_service.analyze_document(file)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats() -> dict:
    """Get list of supported document formats."""
    return {
        "supported_formats": [
            {
                "extension": ".pdf",
                "mime_type": "application/pdf",
                "description": "PDF documents"
            },
            {
                "extension": ".txt",
                "mime_type": "text/plain",
                "description": "Plain text files"
            },
            {
                "extension": ".docx",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "description": "Microsoft Word documents"
            },
            {
                "extension": ".pptx",
                "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "description": "Microsoft PowerPoint presentations"
            },
            {
                "extension": ".xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "description": "Microsoft Excel spreadsheets"
            },
            {
                "extension": ".md",
                "mime_type": "text/markdown",
                "description": "Markdown files"
            }
        ]
    } 