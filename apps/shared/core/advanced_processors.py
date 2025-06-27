"""
Advanced document processors using sophisticated NLP libraries.

These processors provide enhanced functionality beyond the basic examples,
including spaCy-based NER, semantic chunking, and other advanced features.
"""

import re
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from .processor import (
    BaseChunker, BaseNERProcessor, BaseDocumentProcessor,
    ProcessorConfig, ProcessingType, DocumentFormat, DocumentChunk,
    ProcessedDocument, ProcessingContext, ProcessingResult, ProcessingStatus
)


class RecursiveTextChunker(BaseChunker):
    """
    Advanced chunker that recursively splits text using multiple separators.
    Inspired by LangChain's RecursiveCharacterTextSplitter.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="recursive_chunker",
                processing_type=ProcessingType.CHUNKING,
                name="Recursive Text Chunker",
                description="Recursively splits text using multiple separators for better semantic preservation"
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.TEXT, DocumentFormat.MARKDOWN, DocumentFormat.HTML]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {"chunk_size": {"type": "int", "description": "Maximum characters per chunk"}}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "overlap": {"type": "int", "description": "Character overlap", "default": 200},
            "separators": {"type": "list", "description": "Split separators", "default": ["\n\n", "\n", ". ", " "]}
        }
    
    async def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200, **kwargs) -> List[DocumentChunk]:
        separators = kwargs.get('separators', ["\n\n", "\n", ". ", " ", ""])
        
        def split_recursive(text: str, seps: List[str]) -> List[str]:
            if not seps or len(text) <= chunk_size:
                return [text] if text else []
            
            sep = seps[0]
            remaining_seps = seps[1:]
            
            if sep == "":
                return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            parts = text.split(sep)
            chunks = []
            current = ""
            
            for part in parts:
                potential = current + sep + part if current else part
                
                if len(potential) <= chunk_size:
                    current = potential
                else:
                    if current:
                        chunks.append(current)
                    
                    if len(part) > chunk_size:
                        chunks.extend(split_recursive(part, remaining_seps))
                        current = ""
                    else:
                        current = part
            
            if current:
                chunks.append(current)
            
            return chunks
        
        text_chunks = split_recursive(text, separators)
        
        # Create DocumentChunk objects
        result_chunks = []
        for i, chunk_content in enumerate(text_chunks):
            chunk = DocumentChunk(
                chunk_id=f"chunk_{i}_{uuid.uuid4().hex[:8]}",
                document_id="",
                content=chunk_content.strip(),
                start_pos=i * chunk_size,  # Approximate
                end_pos=(i + 1) * chunk_size,
                metadata={"chunk_index": i, "chunk_method": "recursive"}
            )
            result_chunks.append(chunk)
        
        return result_chunks


class SemanticChunker(BaseChunker):
    """
    Semantic chunker that attempts to preserve semantic meaning by using
    sentence boundaries and semantic similarity (simplified version).
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="semantic_chunker",
                processing_type=ProcessingType.CHUNKING,
                name="Semantic Chunker",
                description="Chunks text while preserving semantic meaning using sentence boundaries",
                parameters={
                    "target_chunk_size": 1000,
                    "min_chunk_size": 300,
                    "max_chunk_size": 1500,
                    "sentence_overlap": 1
                }
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [
            DocumentFormat.TEXT,
            DocumentFormat.MARKDOWN
        ]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "target_chunk_size": {
                "type": "int",
                "description": "Target size for chunks (will be flexible around this)",
                "default": 1000,
                "min": 200
            },
            "min_chunk_size": {
                "type": "int",
                "description": "Minimum chunk size",
                "default": 300,
                "min": 100
            },
            "max_chunk_size": {
                "type": "int",
                "description": "Maximum chunk size",
                "default": 1500,
                "min": 500
            },
            "sentence_overlap": {
                "type": "int",
                "description": "Number of sentences to overlap between chunks",
                "default": 1,
                "min": 0
            }
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting. In production, use spaCy or NLTK."""
        # Enhanced sentence splitting pattern
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000,  # This becomes target_chunk_size
        overlap: int = 200,      # This becomes sentence_overlap
        **kwargs
    ) -> List[DocumentChunk]:
        target_size = kwargs.get('target_chunk_size', chunk_size)
        min_size = kwargs.get('min_chunk_size', 300)
        max_size = kwargs.get('max_chunk_size', 1500)
        sentence_overlap = kwargs.get('sentence_overlap', 1)
        
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        current_chunk_sentences = []
        current_length = 0
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed max size
            if current_length + sentence_length > max_size and current_chunk_sentences:
                # Create chunk with current sentences
                chunk_content = ' '.join(current_chunk_sentences)
                chunk = self._create_chunk(chunk_content, chunk_index, sentences, current_chunk_sentences)
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                if sentence_overlap > 0 and len(current_chunk_sentences) > sentence_overlap:
                    current_chunk_sentences = current_chunk_sentences[-sentence_overlap:]
                    current_length = sum(len(s) for s in current_chunk_sentences)
                else:
                    current_chunk_sentences = []
                    current_length = 0
            
            # Add current sentence
            current_chunk_sentences.append(sentence)
            current_length += sentence_length
            
            # Check if we've reached a good chunk size
            if current_length >= target_size and current_length >= min_size:
                # Look ahead to see if there's a good breaking point soon
                if i + 1 < len(sentences):
                    next_sentence_length = len(sentences[i + 1])
                    if current_length + next_sentence_length <= max_size:
                        continue  # Add one more sentence
                
                # Create chunk
                chunk_content = ' '.join(current_chunk_sentences)
                chunk = self._create_chunk(chunk_content, chunk_index, sentences, current_chunk_sentences)
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                if sentence_overlap > 0 and len(current_chunk_sentences) > sentence_overlap:
                    current_chunk_sentences = current_chunk_sentences[-sentence_overlap:]
                    current_length = sum(len(s) for s in current_chunk_sentences)
                else:
                    current_chunk_sentences = []
                    current_length = 0
        
        # Add remaining sentences as final chunk
        if current_chunk_sentences:
            chunk_content = ' '.join(current_chunk_sentences)
            chunk = self._create_chunk(chunk_content, chunk_index, sentences, current_chunk_sentences)
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(
        self, 
        content: str, 
        index: int, 
        all_sentences: List[str], 
        chunk_sentences: List[str]
    ) -> DocumentChunk:
        """Create a DocumentChunk with appropriate metadata."""
        return DocumentChunk(
            chunk_id=f"chunk_{index}_{uuid.uuid4().hex[:8]}",
            document_id="",
            content=content,
            start_pos=None,  # Would need more sophisticated tracking
            end_pos=None,
            metadata={
                "chunk_index": index,
                "chunk_method": "semantic",
                "sentence_count": len(chunk_sentences),
                "word_count": len(content.split()),
                "character_count": len(content)
            }
        )


class EnhancedNERProcessor(BaseNERProcessor):
    """
    Enhanced NER processor with better patterns and entity types.
    In production, this would integrate with spaCy, transformers, or other NLP libraries.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="enhanced_ner",
                processing_type=ProcessingType.NER,
                name="Enhanced NER Processor",
                description="Advanced named entity recognition with improved patterns"
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.TEXT, DocumentFormat.MARKDOWN, DocumentFormat.HTML]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "entity_types": {
                "type": "list",
                "description": "Entity types to extract",
                "default": ["PERSON", "EMAIL", "PHONE", "URL", "DATE", "MONEY"],
                "options": ["PERSON", "EMAIL", "PHONE", "URL", "DATE", "MONEY", "ADDRESS", "ORGANIZATION"]
            },
            "confidence_threshold": {"type": "float", "description": "Min confidence", "default": 0.6}
        }
    
    async def extract_entities(self, text: str, entity_types: Optional[List[str]] = None, **kwargs) -> List[Dict[str, Any]]:
        if entity_types is None:
            entity_types = ["PERSON", "EMAIL", "PHONE", "URL", "DATE", "MONEY"]
        
        confidence_threshold = kwargs.get('confidence_threshold', 0.6)
        entities = []
        
        patterns = {
            "EMAIL": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 0.95),
            "PHONE": (r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}', 0.85),
            "URL": (r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?', 0.9),
            "DATE": (r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b', 0.8),
            "MONEY": (r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:\.\d{2})?\s*(?:dollars?|USD)\b', 0.8),
            "PERSON": (r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', 0.5),
            "ORGANIZATION": (r'\b[A-Z][a-z]+(?:\s+[A-Z&][a-z]*)*\s+(?:Inc|Corp|LLC|Ltd)\b', 0.7),
            "ADDRESS": (r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd)', 0.7)
        }
        
        for entity_type in entity_types:
            if entity_type in patterns:
                pattern, base_confidence = patterns[entity_type]
                
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    if base_confidence >= confidence_threshold:
                        entities.append({
                            "type": entity_type,
                            "text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": base_confidence,
                            "method": "enhanced_regex"
                        })
        
        # Remove overlapping entities
        entities = self._remove_overlapping_entities(entities)
        entities.sort(key=lambda x: x["start"])
        
        return entities
    
    def _remove_overlapping_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping entities, keeping highest confidence."""
        entities.sort(key=lambda x: x["confidence"], reverse=True)
        
        filtered = []
        for entity in entities:
            overlapping = False
            for existing in filtered:
                if (entity["start"] < existing["end"] and entity["end"] > existing["start"]):
                    overlapping = True
                    break
            
            if not overlapping:
                filtered.append(entity)
        
        return filtered


class DocumentSummarizer(BaseDocumentProcessor):
    """
    Simple document summarizer that extracts key sentences.
    In production, this would use more sophisticated NLP models.
    """
    
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="document_summarizer",
                processing_type=ProcessingType.SUMMARIZATION,
                name="Document Summarizer",
                description="Extracts key sentences to create document summaries",
                parameters={
                    "summary_ratio": 0.3,
                    "min_sentences": 2,
                    "max_sentences": 10
                }
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.TEXT, DocumentFormat.MARKDOWN]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "summary_ratio": {
                "type": "float",
                "description": "Ratio of sentences to include in summary",
                "default": 0.3,
                "min": 0.1,
                "max": 0.8
            },
            "min_sentences": {
                "type": "int",
                "description": "Minimum number of sentences in summary",
                "default": 2,
                "min": 1
            },
            "max_sentences": {
                "type": "int",
                "description": "Maximum number of sentences in summary",
                "default": 10,
                "min": 1
            }
        }
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        start_time = datetime.utcnow()
        
        try:
            text_content = document.processed_content or document.raw_content
            if not text_content:
                raise ValueError("No text content found in document")
            
            summary_ratio = kwargs.get('summary_ratio', 0.3)
            min_sentences = kwargs.get('min_sentences', 2)
            max_sentences = kwargs.get('max_sentences', 10)
            
            summary = self._create_summary(text_content, summary_ratio, min_sentences, max_sentences)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.COMPLETED,
                input_document_id=document.document_id,
                output_data={
                    "summary": summary,
                    "summary_length": len(summary),
                    "original_length": len(text_content),
                    "compression_ratio": len(summary) / len(text_content) if text_content else 0
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.FAILED,
                input_document_id=document.document_id,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def _create_summary(
        self, 
        text: str, 
        summary_ratio: float, 
        min_sentences: int, 
        max_sentences: int
    ) -> str:
        """Create a simple extractive summary."""
        # Split into sentences
        sentence_pattern = r'[.!?]+\s+'
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= min_sentences:
            return text
        
        # Calculate target number of sentences
        target_sentences = max(
            min_sentences,
            min(max_sentences, int(len(sentences) * summary_ratio))
        )
        
        # Simple scoring: longer sentences and sentences with more "important" words
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = len(sentence)  # Length-based scoring
            
            # Boost score for sentences with certain keywords
            important_words = ['important', 'significant', 'key', 'main', 'primary', 'conclusion', 'result']
            for word in important_words:
                if word.lower() in sentence.lower():
                    score += 50
            
            # Boost score for sentences at beginning and end
            if i < len(sentences) * 0.2:  # First 20%
                score += 30
            elif i > len(sentences) * 0.8:  # Last 20%
                score += 20
            
            scored_sentences.append((score, i, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        selected_sentences = scored_sentences[:target_sentences]
        
        # Sort selected sentences by original order
        selected_sentences.sort(key=lambda x: x[1])
        
        # Join sentences to create summary
        summary = '. '.join([sentence for _, _, sentence in selected_sentences])
        if not summary.endswith('.'):
            summary += '.'
        
        return summary 