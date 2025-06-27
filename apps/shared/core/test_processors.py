#!/usr/bin/env python3
"""
Test script for document processors.

This script tests the basic functionality of the processor interface
and example implementations.
"""

import asyncio
import sys
from datetime import datetime

# Add the apps directory to the path
sys.path.append('../../..')

from apps.shared.core.processor_service import document_processor_service
from apps.shared.core.processor import ProcessedDocument, ProcessingContext


async def test_processors():
    """Test the document processors."""
    print("🧪 Testing Document Processors")
    print("=" * 50)
    
    # Sample text for testing
    sample_text = """
    Brain_Net is an advanced AI platform designed for document processing and analysis.
    
    Contact us at support@brain-net.com or call +1-555-123-4567 for more information.
    Visit our website at https://brain-net.com to learn more about our services.
    
    Our headquarters is located at 123 Tech Street, San Francisco, CA 94105.
    The platform costs $99.99 per month for premium features.
    
    Founded in 2024, Brain_Net Inc. has been leading the way in AI-powered document analysis.
    John Smith, our CEO, and Jane Doe, our CTO, have over 20 years of combined experience.
    
    We process documents daily from 9:00 AM to 6:00 PM Pacific Time.
    Our success rate is 95% for most document types.
    """
    
    # Mock user and file objects
    class MockUser:
        def __init__(self):
            self.id = 1
    
    class MockFile:
        def __init__(self):
            self.id = 1
            self.file_hash = "test_hash_123"
            self.original_filename = "test_document.txt"
            self.content_type = "text/plain"
    
    user = MockUser()
    user_file = MockFile()
    
    print("📄 Sample text length:", len(sample_text), "characters")
    print()
    
    # Test 1: List available processors
    print("🔍 Test 1: Listing Available Processors")
    print("-" * 30)
    
    processors = document_processor_service.get_available_processors()
    for proc_type, proc_list in processors.items():
        print(f"  {proc_type.upper()}: {len(proc_list)} processors")
        for proc in proc_list:
            print(f"    - {proc['name']} ({proc['processor_id']})")
    print()
    
    # Test 2: Test chunking
    print("🧩 Test 2: Document Chunking")
    print("-" * 30)
    
    try:
        chunks = await document_processor_service.chunk_document(
            user=user,
            user_file=user_file,
            document_content=sample_text,
            chunker_id="fixed_size_chunker",
            chunk_size=200,
            overlap=50
        )
        
        print(f"  ✅ Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:2]):
            print(f"    Chunk {i+1}: {len(chunk.content)} chars")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    # Test 3: Test Recursive Chunker
    print("🔄 Test 3: Recursive Text Chunker")
    print("-" * 30)
    
    try:
        chunks = await document_processor_service.chunk_document(
            user=user,
            user_file=user_file,
            document_content=sample_text,
            chunker_id="recursive_chunker",
            chunk_size=300,
            overlap=50
        )
        
        print(f"  ✅ Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            print(f"    Chunk {i+1}: {len(chunk.content)} chars")
            print(f"      Method: {chunk.metadata.get('chunk_method', 'unknown')}")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    # Test 4: Test Simple NER
    print("🏷️  Test 4: Simple NER Processor")
    print("-" * 30)
    
    try:
        entities = await document_processor_service.extract_entities(
            user=user,
            user_file=user_file,
            document_content=sample_text,
            ner_processor_id="simple_ner",
            entity_types=["PERSON", "EMAIL", "PHONE", "URL", "MONEY"]
        )
        
        print(f"  ✅ Found {len(entities)} entities")
        for entity in entities[:5]:  # Show first 5 entities
            print(f"    {entity['type']}: '{entity['text']}' (confidence: {entity['confidence']:.2f})")
        if len(entities) > 5:
            print(f"    ... and {len(entities) - 5} more entities")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    # Test 5: Test Enhanced NER
    print("🔍 Test 5: Enhanced NER Processor")
    print("-" * 30)
    
    try:
        entities = await document_processor_service.extract_entities(
            user=user,
            user_file=user_file,
            document_content=sample_text,
            ner_processor_id="enhanced_ner",
            entity_types=["PERSON", "EMAIL", "PHONE", "URL", "MONEY", "ORGANIZATION", "ADDRESS"]
        )
        
        print(f"  ✅ Found {len(entities)} entities")
        
        # Group entities by type
        by_type = {}
        for entity in entities:
            entity_type = entity['type']
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        for entity_type, type_entities in by_type.items():
            print(f"    {entity_type}: {len(type_entities)} found")
            for entity in type_entities[:2]:  # Show up to 2 per type
                print(f"      - '{entity['text']}' (conf: {entity['confidence']:.2f})")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    # Test 6: Test Processing Pipeline
    print("⚙️  Test 6: Processing Pipeline")
    print("-" * 30)
    
    try:
        pipeline_config = [
            {
                "processor_id": "metadata_extractor",
                "parameters": {"extract_stats": True}
            },
            {
                "processor_id": "recursive_chunker",
                "parameters": {"chunk_size": 250, "overlap": 50}
            },
            {
                "processor_id": "enhanced_ner",
                "parameters": {"entity_types": ["PERSON", "EMAIL", "URL"], "confidence_threshold": 0.7}
            }
        ]
        
        processed_doc = await document_processor_service.process_user_document(
            user=user,
            user_file=user_file,
            document_content=sample_text,
            processing_config={"pipeline": pipeline_config}
        )
        
        print(f"  ✅ Pipeline completed with {len(processed_doc.processing_results)} steps")
        print(f"  📄 Document chunks: {len(processed_doc.chunks)}")
        print(f"  📊 Metadata keys: {list(processed_doc.metadata.keys())}")
        
        for i, result in enumerate(processed_doc.processing_results):
            print(f"    Step {i+1}: {result.processor_id} - {result.status}")
            if result.processing_time:
                print(f"      Time: {result.processing_time:.3f}s")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    # Test 7: Test Processing Suggestions
    print("💡 Test 7: Processing Suggestions")
    print("-" * 30)
    
    try:
        from apps.shared.core.processor import DocumentFormat
        
        suggestions = await document_processor_service.get_processing_suggestions(
            document_format=DocumentFormat.TEXT
        )
        
        print(f"  ✅ Got {len(suggestions)} suggestions")
        for i, suggestion in enumerate(suggestions):
            print(f"    {i+1}. {suggestion['name']}")
            print(f"       {suggestion['description']}")
            print(f"       Pipeline steps: {len(suggestion['pipeline'])}")
        print()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
    
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_processors()) 