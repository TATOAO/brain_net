from processor_pipeline import (
    AsyncPipeline, 
    AsyncProcessor, 
    execute_processor_code,
    execute_processor_code_from_file,
    create_processor_template,
    list_registered_processors,
    create_processor_from_registry,
    create_pipeline_from_config
)

# Additional helper functions for processor management
def validate_processor_code(code: str) -> bool:
    """Validate processor code for safety and correctness."""
    try:
        # Basic syntax check
        compile(code, '<string>', 'exec')
        
        # Check for required AsyncProcessor inheritance
        if 'AsyncProcessor' not in code:
            raise ValueError("Processor must inherit from AsyncProcessor")
        
        # Check for dangerous imports (basic security)
        dangerous_imports = ['os', 'sys', 'subprocess', 'eval', 'exec']
        for dangerous in dangerous_imports:
            if f"import {dangerous}" in code or f"from {dangerous}" in code:
                raise ValueError(f"Dangerous import '{dangerous}' not allowed")
        
        return True
    except Exception as e:
        raise ValueError(f"Code validation failed: {str(e)}")

def create_processor_instance(processor_code: str, config: dict = None) -> AsyncProcessor:
    """Create a processor instance from code."""
    config = config or {}
    
    # Validate the code first
    validate_processor_code(processor_code)
    
    # Execute the code to get the processor class
    processor_class = execute_processor_code(processor_code)
    
    # Create and return instance
    return processor_class(config)

def get_builtin_processors():
    """Get list of built-in processors available in the system."""
    return [
        {
            "name": "Text Chunker",
            "description": "Splits text into smaller chunks for processing",
            "processor_type": "builtin",
            "capabilities": ["text_chunking", "text_processing"],
            "input_types": ["str", "text"],
            "output_types": ["List[str]", "chunks"]
        },
        {
            "name": "Vector Generator", 
            "description": "Generates vector embeddings from text",
            "processor_type": "builtin",
            "capabilities": ["vector_generation", "embedding"],
            "input_types": ["List[str]", "chunks"],
            "output_types": ["Dict[str, Any]", "vectors"]
        }
    ]