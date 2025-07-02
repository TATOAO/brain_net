"""
Document service for Brain_Net LLM Service
"""

from typing import List
from fastapi import UploadFile
from app.core.database import DatabaseManager
from app.schemas.documents import (
    DocumentProcessResponse, DocumentMetadata, DocumentChunk,
    EmbeddingRequest, EmbeddingResponse
)
from app.core.logging import LLMLogger
from apps.shared.core.processor_service import document_processor_service
from apps.shared.models.user import User
from apps.shared.models.file import UserFile

logger = LLMLogger("documents")


class DocumentService:
    """Service for handling document operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def process_document(self, file: UploadFile, chunk_size: int, chunk_overlap: int) -> DocumentProcessResponse:
        """Process a document and extract text chunks."""
        import time
        start_time = time.time()
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        document_content = content.decode('utf-8', errors='ignore')
        
        # Create mock user and file objects for processing
        # In a real implementation, you'd get these from the request context
        class MockUser:
            def __init__(self, user_id: int = 1):
                self.id = user_id
        
        class MockUserFile:
            def __init__(self, filename: str, content_type: str, file_size: int):
                self.id = 1
                self.file_hash = f"hash_{filename}_{file_size}"
                self.original_filename = filename
                self.content_type = content_type
                self.file_size = file_size
                self.uploaded_at = None
        
        user = MockUser()
        user_file = MockUserFile(file.filename, file.content_type, len(content))
        
        # Use shared processor service to chunk the document
        chunks = await document_processor_service.chunk_document(
            user=user,
            user_file=user_file,
            document_content=document_content,
            chunker_id="fixed_size_chunker",
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        processing_time = time.time() - start_time
        
        return DocumentProcessResponse(
            document_id=f"doc_{user_file.file_hash[:8]}",
            filename=file.filename,
            chunks_created=len(chunks),
            processing_time=processing_time,
            metadata={
                "size": len(content), 
                "type": file.content_type,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        )
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for text chunks."""
        # TODO: Implement embedding generation
        return EmbeddingResponse(
            embeddings=[],
            model=request.model or "placeholder",
            dimension=1536,
            processing_time=0.5
        )
    
    async def get_document_metadata(self, document_id: str) -> DocumentMetadata:
        """Get metadata for a document."""
        # TODO: Implement metadata retrieval
        return DocumentMetadata(
            id=document_id,
            filename="placeholder.txt",
            size=0,
            content_type="text/plain",
            created_at="2024-01-01T00:00:00Z",
            chunk_count=0
        )
    
    async def get_document_chunks(self, document_id: str, limit: int, offset: int) -> List[DocumentChunk]:
        """Get chunks for a document."""
        # TODO: Implement chunk retrieval
        return []
    
    async def extract_text(self, file: UploadFile) -> str:
        """Extract raw text from a document."""
        content = await file.read()
        await file.seek(0)  # Reset file pointer for potential reuse
        return content.decode('utf-8', errors='ignore')
    
    async def analyze_document(self, file: UploadFile) -> dict:
        """Analyze document structure and content."""
        import re
        
        # Read file content
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        document_content = content.decode('utf-8', errors='ignore')
        
        # Basic text analysis
        word_count = len(document_content.split())
        
        # Count paragraphs (separated by double newlines or single newlines with significant content)
        paragraphs = len([p for p in re.split(r'\n\s*\n', document_content) if p.strip()])
        
        # Estimate sections (lines that might be headers - short lines, possibly with special formatting)
        lines = document_content.split('\n')
        potential_sections = 0
        for line in lines:
            line = line.strip()
            # Heuristic: short lines (likely headers), or lines with special chars, or all caps
            if line and (len(line) < 50 and len(line.split()) < 8) or line.isupper():
                potential_sections += 1
        
        # Very basic language detection (just checking for common English words)
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words_lower = document_content.lower().split()
        english_count = sum(1 for word in english_words if word in words_lower[:100])  # Check first 100 words
        language = "en" if english_count > 5 else "unknown"
        
        return {
            "filename": file.filename,
            "size": len(content),
            "type": file.content_type,
            "language": language,
            "word_count": word_count,
            "character_count": len(document_content),
            "structure": {
                "sections": potential_sections,
                "paragraphs": paragraphs,
                "lines": len(lines),
                "tables": document_content.count('|'),  # Simple table detection
                "images": 0  # Text files don't contain images
            }
        } 