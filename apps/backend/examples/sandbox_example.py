"""
Example script demonstrating Python sandbox usage for AI agents
"""

import asyncio
import json
from datetime import datetime

from app.services.sandbox_service import SandboxService
from app.core.database import get_db_session
from app.core.config import get_settings


async def example_data_analysis():
    """Example: Data analysis agent using sandbox."""
    print("🔍 Data Analysis Agent Example")
    print("=" * 50)
    
    # Initialize sandbox service
    db_session = await get_db_session()
    service = SandboxService(db_session)
    
    try:
        # Create sandbox
        sandbox_id = await service.create_agent_sandbox(
            user_id=1,
            config={
                'max_execution_time': 30,
                'max_memory_mb': 256,
                'enable_debugging': True
            }
        )
        print(f"✅ Created sandbox: {sandbox_id}")
        
        # Example analysis code
        analysis_code = """
# Get user data
users = await db_query('SELECT * FROM users LIMIT 10')
debug(f'Retrieved {len(users)} users', 'INFO')

# Analyze user patterns
user_stats = {
    'total_users': len(users),
    'users_with_email': len([u for u in users if u.get('email')]),
    'creation_dates': [u.get('created_at') for u in users if u.get('created_at')]
}

# Extract email domains
email_domains = []
for user in users:
    if user.get('email') and '@' in user['email']:
        domain = user['email'].split('@')[1]
        email_domains.append(domain)

# Count domain frequency
from collections import Counter
domain_counts = Counter(email_domains)

debug(f'Found {len(email_domains)} email domains', 'INFO')
inspect_var('domain_counts', dict(domain_counts))

# Set result
__result__ = {
    'user_statistics': user_stats,
    'email_domains': dict(domain_counts),
    'analysis_timestamp': datetime.utcnow().isoformat()
}
"""
        
        # Execute analysis
        print("\n🚀 Executing analysis...")
        result = await service.execute_code(sandbox_id, analysis_code)
        
        if result.status == 'completed':
            print("✅ Analysis completed successfully!")
            print(f"📊 Results: {json.dumps(result.result, indent=2)}")
            print(f"🐛 Debug info: {result.debug_info}")
        else:
            print(f"❌ Analysis failed: {result.error}")
            print(f"📝 Output: {result.stdout}")
            print(f"🚨 Errors: {result.stderr}")
        
        # Get database schema
        print("\n🏗️  Database Schema:")
        schema = await service.get_database_schema(sandbox_id)
        print(f"📋 Tables: {schema['tables']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        await service.cleanup_sandbox(sandbox_id)
        print(f"🧹 Cleaned up sandbox: {sandbox_id}")


async def example_knowledge_extraction():
    """Example: Knowledge extraction agent using sandbox."""
    print("\n🧠 Knowledge Extraction Agent Example")
    print("=" * 50)
    
    # Initialize sandbox service
    db_session = await get_db_session()
    service = SandboxService(db_session)
    
    try:
        # Create sandbox
        sandbox_id = await service.create_agent_sandbox(
            user_id=1,
            config={
                'max_execution_time': 45,
                'max_memory_mb': 512,
                'enable_debugging': True
            }
        )
        print(f"✅ Created sandbox: {sandbox_id}")
        
        # Knowledge extraction code
        extraction_code = """
import re
from collections import Counter

# Get documents for processing
documents = await db_query('SELECT * FROM documents WHERE processed = false LIMIT 5')
debug(f'Processing {len(documents)} documents', 'INFO')

if not documents:
    debug('No unprocessed documents found', 'WARNING')
    __result__ = {'message': 'No documents to process'}
else:
    extracted_knowledge = []
    
    for doc in documents:
        debug(f'Processing document {doc["id"]}', 'INFO')
        
        content = doc.get('content', '')
        title = doc.get('title', 'Untitled')
        
        # Extract entities
        emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', content)
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        
        # Extract keywords
        words = re.findall(r'\\b\\w+\\b', content.lower())
        word_freq = Counter(words)
        keywords = [word for word, freq in word_freq.most_common(10) if len(word) > 3]
        
        knowledge = {
            'document_id': doc['id'],
            'title': title,
            'content_length': len(content),
            'entities': {
                'emails': emails,
                'urls': urls
            },
            'keywords': keywords,
            'word_count': len(words),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        extracted_knowledge.append(knowledge)
        inspect_var(f'doc_{doc["id"]}_knowledge', knowledge)
        
        # Mark as processed (in a real scenario)
        debug(f'Completed processing document {doc["id"]}', 'INFO')
    
    __result__ = {
        'processed_documents': len(documents),
        'extracted_knowledge': extracted_knowledge,
        'total_entities': sum(len(k['entities']['emails']) + len(k['entities']['urls']) for k in extracted_knowledge)
    }
"""
        
        # Execute extraction
        print("\n🚀 Executing knowledge extraction...")
        result = await service.execute_code(sandbox_id, extraction_code)
        
        if result.status == 'completed':
            print("✅ Knowledge extraction completed!")
            print(f"📊 Results: {json.dumps(result.result, indent=2)}")
        else:
            print(f"❌ Extraction failed: {result.error}")
            print(f"📝 Output: {result.stdout}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        await service.cleanup_sandbox(sandbox_id)
        print(f"🧹 Cleaned up sandbox: {sandbox_id}")


async def example_debugging():
    """Example: Debugging agent using sandbox."""
    print("\n🐛 Debugging Agent Example")
    print("=" * 50)
    
    # Initialize sandbox service
    db_session = await get_db_session()
    service = SandboxService(db_session)
    
    try:
        # Create sandbox
        sandbox_id = await service.create_agent_sandbox(
            user_id=1,
            config={
                'max_execution_time': 30,
                'max_memory_mb': 256,
                'enable_debugging': True
            }
        )
        print(f"✅ Created sandbox: {sandbox_id}")
        
        # Debug code with potential issues
        debug_code = """
debug('Starting debugging session', 'INFO')

# Test data
test_data = [1, 2, 3, "4", 5, None, 7, 8, 9]
debug(f'Test data: {test_data}', 'INFO')
inspect_var('test_data', test_data)

# Process data with debugging
processed = []
errors = []

for i, item in enumerate(test_data):
    debug(f'Processing item {i}: {item}', 'DEBUG')
    
    try:
        if item is None:
            debug(f'None value at index {i}', 'WARNING')
            continue
            
        # Try to convert to int
        num = int(item)
        result = num * 2
        processed.append(result)
        debug(f'Successfully processed {item} -> {result}', 'DEBUG')
        
    except ValueError as e:
        debug(f'Error processing item {item}: {e}', 'ERROR')
        errors.append({'index': i, 'value': item, 'error': str(e)})
    except Exception as e:
        debug(f'Unexpected error with item {item}: {e}', 'ERROR')
        errors.append({'index': i, 'value': item, 'error': str(e)})

debug(f'Processing complete. Processed: {len(processed)}, Errors: {len(errors)}', 'INFO')
inspect_var('processed', processed)
inspect_var('errors', errors)

__result__ = {
    'original_data': test_data,
    'processed_data': processed,
    'errors': errors,
    'debug_summary': get_debug_info()
}
"""
        
        # Execute debugging
        print("\n🚀 Executing debugging session...")
        result = await service.execute_code(sandbox_id, debug_code)
        
        if result.status == 'completed':
            print("✅ Debugging session completed!")
            print(f"📊 Results: {json.dumps(result.result, indent=2)}")
            print(f"🐛 Debug logs: {len(result.debug_info.get('recent_logs', []))} entries")
        else:
            print(f"❌ Debugging failed: {result.error}")
        
        # Get execution history
        print("\n📜 Execution History:")
        history = await service.get_execution_history(sandbox_id)
        for execution in history:
            print(f"  - {execution['execution_id']}: {execution['status']} ({execution['execution_time']:.2f}s)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up
        await service.cleanup_sandbox(sandbox_id)
        print(f"🧹 Cleaned up sandbox: {sandbox_id}")


async def example_quick_execution():
    """Example: Quick execution for simple tasks."""
    print("\n⚡ Quick Execution Example")
    print("=" * 50)
    
    # Initialize sandbox service
    db_session = await get_db_session()
    service = SandboxService(db_session)
    
    try:
        # Quick execution - creates sandbox, executes, and cleans up automatically
        simple_code = """
# Simple calculation
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
average = result / len(numbers)

debug(f'Sum: {result}, Average: {average}', 'INFO')

__result__ = {
    'numbers': numbers,
    'sum': result,
    'average': average,
    'count': len(numbers)
}
"""
        
        print("🚀 Executing quick task...")
        # This would use the quick-execute endpoint
        # For now, simulate with regular execution
        sandbox_id = await service.create_agent_sandbox(user_id=1)
        result = await service.execute_code(sandbox_id, simple_code)
        await service.cleanup_sandbox(sandbox_id)
        
        if result.status == 'completed':
            print("✅ Quick execution completed!")
            print(f"📊 Results: {json.dumps(result.result, indent=2)}")
        else:
            print(f"❌ Quick execution failed: {result.error}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("🚀 Python Sandbox Examples for AI Agents")
    print("=" * 60)
    
    try:
        # Run examples
        await example_data_analysis()
        await example_knowledge_extraction()
        await example_debugging()
        await example_quick_execution()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()

# python -m examples.sandbox_example
if __name__ == "__main__":
    # Run examples
    asyncio.run(main()) 