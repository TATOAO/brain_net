"""
Visual Processor Integration for Brain_Net

This module provides integration utilities for the doc_visual_parsor processors,
showing how to register them with the processor registry and use them in pipelines.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import shutil

from .processor import (
    processor_registry,
    DocVisualParsorProcessor,
    VisualStructureChunker,
    ProcessedDocument,
    ProcessingContext,
    ProcessingPipeline,
    ProcessingType,
    DocumentFormat
)


def register_visual_processors():
    """
    Register all visual processing processors with the global registry.
    
    Call this function during application startup to make the processors available.
    """
    # Register the main visual parser processor
    visual_parser = DocVisualParsorProcessor()
    processor_registry.register_processor(visual_parser)
    
    # Register the structure-aware chunker
    structure_chunker = VisualStructureChunker()
    processor_registry.register_processor(structure_chunker)
    
    print("Visual processors registered successfully:")
    print(f"- {visual_parser.config.name} (ID: {visual_parser.processor_id})")
    print(f"- {structure_chunker.config.name} (ID: {structure_chunker.processor_id})")


async def process_document_with_visual_parsing(
    file_path: str,
    user_id: int,
    document_id: str,
    file_hash: str,
    use_structure_chunking: bool = True,
    max_chunk_size: int = 1000,
    preserve_sections: bool = True
) -> ProcessedDocument:
    """
    Process a document using visual parsing and structure-aware chunking.
    
    Args:
        file_path: Path to the document file
        user_id: User ID for processing context
        document_id: Unique document identifier
        file_hash: File hash for tracking
        use_structure_chunking: Whether to use structure-aware chunking
        max_chunk_size: Maximum chunk size for structure chunking
        preserve_sections: Whether to preserve section boundaries
        
    Returns:
        ProcessedDocument with visual parsing results and chunks
    """
    # Determine document format
    file_ext = Path(file_path).suffix.lower()
    if file_ext == '.pdf':
        content_type = DocumentFormat.PDF.value
    elif file_ext == '.docx':
        content_type = DocumentFormat.DOCX.value
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Create processed document
    document = ProcessedDocument(
        document_id=document_id,
        original_filename=Path(file_path).name,
        file_hash=file_hash,
        user_id=user_id,
        content_type=content_type
    )
    
    # Create processing context
    context = ProcessingContext(
        user_id=user_id,
        document_id=document_id,
        file_hash=file_hash,
        processing_pipeline=["doc_visual_parsor", "visual_structure_chunker"] if use_structure_chunking else ["doc_visual_parsor"]
    )
    
    # Create processing pipeline
    pipeline = ProcessingPipeline(processor_registry)
    
    # Define pipeline configuration
    pipeline_config = [
        {
            "processor_id": "doc_visual_parsor",
            "parameters": {
                "file_path": file_path,
                "confidence_threshold": 0.5,
                "use_llm_structure": True
            }
        }
    ]
    
    if use_structure_chunking:
        pipeline_config.append({
            "processor_id": "visual_structure_chunker",
            "parameters": {
                "max_chunk_size": max_chunk_size,
                "preserve_sections": preserve_sections,
                "include_headers": True,
                "chunk_overlap": 100
            }
        })
    
    # Execute the pipeline
    results = await pipeline.execute_pipeline(document, context, pipeline_config)
    
    return document


async def batch_process_documents(
    file_paths: List[str],
    user_id: int,
    use_structure_chunking: bool = True,
    max_concurrent: int = 3
) -> List[ProcessedDocument]:
    """
    Process multiple documents in parallel using visual parsing.
    
    Args:
        file_paths: List of document file paths
        user_id: User ID for processing context
        use_structure_chunking: Whether to use structure-aware chunking
        max_concurrent: Maximum number of concurrent processing tasks
        
    Returns:
        List of ProcessedDocument objects
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_document(file_path: str, index: int) -> ProcessedDocument:
        async with semaphore:
            document_id = f"doc_{index}_{Path(file_path).stem}"
            file_hash = f"hash_{index}_{Path(file_path).name}"
            
            return await process_document_with_visual_parsing(
                file_path=file_path,
                user_id=user_id,
                document_id=document_id,
                file_hash=file_hash,
                use_structure_chunking=use_structure_chunking
            )
    
    # Process all documents concurrently
    tasks = [
        process_single_document(file_path, i) 
        for i, file_path in enumerate(file_paths)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return successful results
    successful_results = [
        result for result in results 
        if isinstance(result, ProcessedDocument)
    ]
    
    # Log any exceptions
    exceptions = [
        result for result in results 
        if isinstance(result, Exception)
    ]
    
    if exceptions:
        print(f"Processing errors occurred for {len(exceptions)} documents:")
        for i, exc in enumerate(exceptions):
            print(f"  Error {i+1}: {str(exc)}")
    
    return successful_results


def create_visual_processing_pipeline_config(
    enable_visual_parsing: bool = True,
    enable_structure_chunking: bool = True,
    enable_ner: bool = False,
    chunking_params: Optional[Dict[str, Any]] = None,
    visual_params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Create a pipeline configuration for visual document processing.
    
    Args:
        enable_visual_parsing: Whether to include visual parsing step
        enable_structure_chunking: Whether to include structure-aware chunking
        enable_ner: Whether to include NER processing (requires NER processor)
        chunking_params: Parameters for structure chunking
        visual_params: Parameters for visual parsing
        
    Returns:
        Pipeline configuration list
    """
    pipeline_config = []
    
    # Default parameters
    default_visual_params = {
        "confidence_threshold": 0.5,
        "use_llm_structure": True,
        "chunk_size": 10
    }
    
    default_chunking_params = {
        "max_chunk_size": 1000,
        "preserve_sections": True,
        "include_headers": True,
        "chunk_overlap": 100
    }
    
    # Merge with user-provided parameters
    if visual_params:
        default_visual_params.update(visual_params)
    if chunking_params:
        default_chunking_params.update(chunking_params)
    
    # Add visual parsing step
    if enable_visual_parsing:
        pipeline_config.append({
            "processor_id": "doc_visual_parsor",
            "parameters": default_visual_params
        })
    
    # Add structure-aware chunking step
    if enable_structure_chunking:
        pipeline_config.append({
            "processor_id": "visual_structure_chunker",
            "parameters": default_chunking_params
        })
    
    # Add NER step if requested (assuming you have an NER processor)
    if enable_ner:
        pipeline_config.append({
            "processor_id": "spacy_ner",  # Example NER processor ID
            "parameters": {
                "entity_types": ["PERSON", "ORG", "LOC", "DATE"]
            }
        })
    
    return pipeline_config


async def validate_visual_processing_setup() -> Dict[str, Any]:
    """
    Validate that the visual processing setup is working correctly.
    
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "processors_registered": False,
        "doc_chunking_available": False,
        "processors_info": {},
        "errors": []
    }
    
    try:
        # Check if processors are registered
        visual_parser = processor_registry.get_processor("doc_visual_parsor")
        structure_chunker = processor_registry.get_processor("visual_structure_chunker")
        
        if visual_parser and structure_chunker:
            validation_result["processors_registered"] = True
            validation_result["processors_info"] = {
                "visual_parser": visual_parser.get_processor_info(),
                "structure_chunker": structure_chunker.get_processor_info()
            }
        else:
            validation_result["errors"].append("Visual processors not registered")
        
        # Check if doc_chunking library is available
        try:
            import doc_chunking
            validation_result["doc_chunking_available"] = True
        except ImportError:
            validation_result["errors"].append("doc_chunking library not available")
        
    except Exception as e:
        validation_result["errors"].append(f"Validation error: {str(e)}")
    
    return validation_result


# Example usage functions

async def example_process_single_pdf():
    """Example: Process a single PDF document with visual parsing."""
    # Register processors first
    register_visual_processors()
    
    # Example file path (adjust as needed)
    file_path = "/path/to/your/document.pdf"
    
    if not Path(file_path).exists():
        print(f"Example file not found: {file_path}")
        return
    
    try:
        document = await process_document_with_visual_parsing(
            file_path=file_path,
            user_id=1,
            document_id="example_doc_1",
            file_hash="example_hash_1",
            use_structure_chunking=True,
            max_chunk_size=800,
            preserve_sections=True
        )
        
        print(f"Document processed successfully!")
        print(f"- Sections found: {len(document.document_sections)}")
        print(f"- Chunks created: {len(document.chunks)}")
        print(f"- Processing results: {len(document.processing_results)}")
        
        # Print section structure
        print("\nDocument Structure:")
        for i, section in enumerate(document.document_sections):
            print(f"  {i+1}. {section.title} (Level {section.level})")
            print(f"     Content length: {len(section.content)} chars")
            for j, subsection in enumerate(section.sub_sections):
                print(f"     {i+1}.{j+1} {subsection.title} (Level {subsection.level})")
        
        # Print chunk information
        print(f"\nChunks:")
        for i, chunk in enumerate(document.chunks[:5]):  # Show first 5 chunks
            print(f"  Chunk {i+1}: {chunk.section_title} (Level {chunk.section_level})")
            print(f"    Content: {chunk.content[:100]}...")
            print(f"    Size: {len(chunk.content)} chars")
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")


async def example_batch_process():
    """Example: Batch process multiple documents."""
    # Register processors first
    register_visual_processors()
    
    # Example file paths (adjust as needed)
    file_paths = [
        "/path/to/document1.pdf",
        "/path/to/document2.docx",
        "/path/to/document3.pdf"
    ]
    
    # Filter existing files
    existing_files = [f for f in file_paths if Path(f).exists()]
    
    if not existing_files:
        print("No example files found")
        return
    
    try:
        documents = await batch_process_documents(
            file_paths=existing_files,
            user_id=1,
            use_structure_chunking=True,
            max_concurrent=2
        )
        
        print(f"Batch processing completed!")
        print(f"Successfully processed {len(documents)} documents")
        
        for i, doc in enumerate(documents):
            print(f"\nDocument {i+1}: {doc.original_filename}")
            print(f"  Sections: {len(doc.document_sections)}")
            print(f"  Chunks: {len(doc.chunks)}")
            print(f"  Status: {doc.processing_results[-1].status if doc.processing_results else 'Unknown'}")
        
    except Exception as e:
        print(f"Error in batch processing: {str(e)}")


if __name__ == "__main__":
    # Run validation
    async def run_validation():
        register_visual_processors()
        validation = await validate_visual_processing_setup()
        print("Visual Processing Setup Validation:")
        print(f"Processors registered: {validation['processors_registered']}")
        print(f"doc_chunking available: {validation['doc_chunking_available']}")
        if validation['errors']:
            print("Errors:")
            for error in validation['errors']:
                print(f"  - {error}")
        else:
            print("Setup is valid!")
    
    # Run the validation
    asyncio.run(run_validation()) 