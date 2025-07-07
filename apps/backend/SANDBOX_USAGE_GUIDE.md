# Python Sandbox Environment for AI Agents

## Overview

The Python sandbox environment provides a secure, monitored execution environment for AI agents to process data, debug code, and interact with databases in your knowledge base project.

## Features

### 🔒 Security
- **Restricted imports**: Only safe modules are allowed
- **Code validation**: Dangerous functions are blocked
- **Resource limits**: Memory, CPU, and execution time limits
- **Process isolation**: Each sandbox runs in isolation

### 📊 Database Access
- **Secure queries**: Read-only access with query validation
- **Schema inspection**: Get table structures and metadata
- **Query logging**: All database operations are logged

### 🐛 Debugging
- **Step-by-step execution**: Debug code line by line
- **Variable inspection**: Track variable changes over time
- **Comprehensive logging**: Multiple log levels and detailed information
- **Execution history**: View past executions and their results

### 🔧 Resource Management
- **Memory monitoring**: Automatic memory usage tracking
- **CPU limits**: Prevent excessive CPU usage
- **Timeout protection**: Execution time limits
- **Automatic cleanup**: Expired sandboxes are cleaned up automatically

## Quick Start

### 1. Create a Sandbox

```python
from app.services.sandbox_service import SandboxService
from app.core.database import get_db_session

# Create sandbox service
db_session = await get_db_session()
service = SandboxService(db_session)

# Create sandbox for user
sandbox_id = await service.create_agent_sandbox(
    user_id=1,
    config={
        'max_execution_time': 30,
        'max_memory_mb': 256,
        'enable_debugging': True
    }
)
```

### 2. Execute Code

```python
# Simple data processing
code = """
# Get data from database
users = await db_query('SELECT * FROM users LIMIT 10')
debug(f'Retrieved {len(users)} users', 'INFO')

# Process data
processed_users = []
for user in users:
    processed_user = {
        'id': user['id'],
        'name': user.get('name', 'Unknown'),
        'email': user.get('email', ''),
        'domain': user.get('email', '').split('@')[-1] if '@' in user.get('email', '') else 'unknown'
    }
    processed_users.append(processed_user)

# Set result
__result__ = {
    'total_users': len(users),
    'processed_users': processed_users
}
"""

result = await service.execute_code(sandbox_id, code)
print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Debug info: {result.debug_info}")
```

### 3. Database Operations

```python
# Query database
query_result = await service.query_database(
    sandbox_id,
    "SELECT COUNT(*) as user_count FROM users WHERE created_at > :date",
    {"date": "2024-01-01"}
)

# Get database schema
schema = await service.get_database_schema(sandbox_id)
print(f"Available tables: {schema['tables']}")
```

### 4. Debug Code

```python
# Debug code step by step
debug_code = """
data = [1, 2, 3, 4, 5]
debug('Starting processing', 'INFO')

result = []
for item in data:
    processed = item * 2
    result.append(processed)
    debug(f'Processed item {item} -> {processed}', 'DEBUG')

debug('Processing complete', 'INFO')
__result__ = result
"""

async for debug_step in service.debug_code(sandbox_id, debug_code):
    print(f"Line {debug_step['line_number']}: {debug_step['line_code']}")
    print(f"Result: {debug_step['result'].status}")
    print(f"Variables: {debug_step['state']['variables']}")
```

## API Endpoints

### Sandbox Management

- `POST /sandbox/create` - Create new sandbox
- `GET /sandbox/{sandbox_id}/status` - Get sandbox status
- `DELETE /sandbox/{sandbox_id}` - Clean up sandbox

### Code Execution

- `POST /sandbox/{sandbox_id}/execute` - Execute code
- `POST /sandbox/{sandbox_id}/debug` - Debug code step by step

### Database Access

- `POST /sandbox/{sandbox_id}/database/query` - Execute database query
- `GET /sandbox/{sandbox_id}/database/schema` - Get database schema

### Agent Helpers

- `POST /sandbox/agent/quick-execute` - Quick execution (creates sandbox, executes, cleans up)
- `POST /sandbox/agent/analyze-data` - Quick data analysis
- `GET /sandbox/{sandbox_id}/help/functions` - Get available functions
- `GET /sandbox/{sandbox_id}/help/examples` - Get code examples

## Available Functions in Sandbox

### Database Functions
```python
# Execute SQL query
results = await db_query("SELECT * FROM users WHERE id = :id", {"id": 1})

# Get list of tables
tables = await db_tables()

# Get table schema
schema = await db_schema("users")
```

### Debug Functions
```python
# Log debug message
debug("Processing started", "INFO")

# Inspect variable
inspect_var("my_data", data)

# Get debug summary
debug_info = get_debug_info()
```

### Built-in Functions
```python
# Standard Python functions are available
print("Hello, World!")
len([1, 2, 3])
type("string")
str(123)
```

## Use Cases

### 1. Data Analysis Agent

```python
# Agent analyzes user behavior patterns
analysis_code = """
# Get user activity data
activities = await db_query('''
    SELECT user_id, action, timestamp 
    FROM user_activities 
    WHERE timestamp > NOW() - INTERVAL '7 days'
    ORDER BY timestamp
''')

debug(f'Analyzing {len(activities)} activities', 'INFO')

# Analyze patterns
user_patterns = {}
for activity in activities:
    user_id = activity['user_id']
    action = activity['action']
    
    if user_id not in user_patterns:
        user_patterns[user_id] = {}
    
    if action not in user_patterns[user_id]:
        user_patterns[user_id][action] = 0
    
    user_patterns[user_id][action] += 1

# Find most active users
most_active = sorted(user_patterns.items(), 
                    key=lambda x: sum(x[1].values()), 
                    reverse=True)[:10]

__result__ = {
    'total_activities': len(activities),
    'unique_users': len(user_patterns),
    'most_active_users': most_active,
    'analysis_timestamp': datetime.utcnow().isoformat()
}
"""

result = await service.execute_code(sandbox_id, analysis_code)
```

### 2. Knowledge Extraction Agent

```python
# Agent extracts knowledge from documents
extraction_code = """
import re
from collections import Counter

# Get unprocessed documents
documents = await db_query('''
    SELECT id, title, content 
    FROM documents 
    WHERE processed = false 
    LIMIT 20
''')

debug(f'Processing {len(documents)} documents', 'INFO')

extracted_knowledge = []

for doc in documents:
    # Extract entities
    content = doc['content']
    
    # Extract emails
    emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', content)
    
    # Extract phone numbers
    phones = re.findall(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', content)
    
    # Extract URLs
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
    
    # Extract keywords
    words = re.findall(r'\\b\\w+\\b', content.lower())
    word_freq = Counter(words)
    keywords = [word for word, freq in word_freq.most_common(10) if len(word) > 3]
    
    knowledge = {
        'document_id': doc['id'],
        'title': doc['title'],
        'entities': {
            'emails': emails,
            'phones': phones,
            'urls': urls
        },
        'keywords': keywords,
        'word_count': len(words),
        'extracted_at': datetime.utcnow().isoformat()
    }
    
    extracted_knowledge.append(knowledge)
    
    # Mark as processed
    await db_query(
        'UPDATE documents SET processed = true WHERE id = :id',
        {'id': doc['id']}
    )
    
    debug(f'Processed document {doc["id"]}', 'DEBUG')

__result__ = {
    'processed_documents': len(documents),
    'extracted_knowledge': extracted_knowledge
}
"""

result = await service.execute_code(sandbox_id, extraction_code)
```

### 3. Pipeline Debugging Agent

```python
# Agent debugs processor pipeline issues
debug_code = """
debug('Starting pipeline debugging', 'INFO')

# Check data flow
try:
    # Step 1: Input validation
    input_data = await db_query('SELECT * FROM pipeline_input LIMIT 5')
    debug(f'Input data: {len(input_data)} records', 'INFO')
    inspect_var('input_data', input_data)
    
    # Step 2: Processing logic
    processed = []
    for item in input_data:
        if 'content' in item and item['content']:
            processed_item = {
                'id': item['id'],
                'content_length': len(item['content']),
                'has_content': True
            }
        else:
            processed_item = {
                'id': item['id'],
                'content_length': 0,
                'has_content': False
            }
            debug(f'Missing content for item {item["id"]}', 'WARNING')
        
        processed.append(processed_item)
    
    debug(f'Processed {len(processed)} items', 'INFO')
    inspect_var('processed', processed)
    
    # Step 3: Output validation
    valid_output = [item for item in processed if item['has_content']]
    debug(f'Valid output: {len(valid_output)} items', 'INFO')
    
    __result__ = {
        'input_count': len(input_data),
        'processed_count': len(processed),
        'valid_output_count': len(valid_output),
        'debug_summary': get_debug_info()
    }
    
except Exception as e:
    debug(f'Error in pipeline: {str(e)}', 'ERROR')
    __result__ = {
        'error': str(e),
        'debug_summary': get_debug_info()
    }
"""

result = await service.execute_code(sandbox_id, debug_code)
```

## Best Practices

### 1. Resource Management
```python
# Always set reasonable limits
config = {
    'max_execution_time': 30,  # Don't exceed 30 seconds
    'max_memory_mb': 256,      # Limit memory usage
    'enable_debugging': True    # Enable debugging for development
}
```

### 2. Error Handling
```python
# Always handle errors gracefully
try:
    result = await service.execute_code(sandbox_id, code)
    if result.status == 'failed':
        print(f"Execution failed: {result.error}")
        print(f"Debug info: {result.debug_info}")
except Exception as e:
    print(f"Service error: {e}")
```

### 3. Database Queries
```python
# Use parameterized queries
query = "SELECT * FROM users WHERE created_at > :date"
params = {"date": "2024-01-01"}
results = await service.query_database(sandbox_id, query, params)
```

### 4. Debugging
```python
# Use debug functions liberally
debug("Starting processing", "INFO")
inspect_var("data", my_data)
debug("Processing complete", "INFO")
```

### 5. Cleanup
```python
# Always clean up when done
await service.cleanup_sandbox(sandbox_id)
```

## Security Considerations

### Allowed Modules
- Standard Python modules: `json`, `datetime`, `math`, `random`, `collections`
- Data processing: `pandas`, `numpy`
- Text processing: `re`, `string`
- HTTP clients: `requests`, `aiohttp`

### Blocked Operations
- File system access: `os`, `sys`, `subprocess`
- Dynamic code execution: `eval`, `exec`, `compile`
- Network access: `socket`, `urllib` (except `urllib.parse`)
- System introspection: `globals`, `locals`, `vars`

### Resource Limits
- Memory: 256MB default (configurable)
- CPU: 50% maximum usage
- Execution time: 30 seconds default
- Open files: 100 maximum
- Threads: 10 maximum

## Monitoring and Metrics

### Get Sandbox Statistics
```python
stats = await service.get_sandbox_statistics()
print(f"Active sandboxes: {stats['active_sandboxes']}")
print(f"Success rate: {stats['success_rate']:.2f}%")
print(f"Average execution time: {stats['average_execution_time']:.2f}s")
```

### Execution History
```python
history = await service.get_execution_history(sandbox_id)
for execution in history:
    print(f"Execution {execution['execution_id']}: {execution['status']}")
```

## Integration with Processor Pipeline

The sandbox can be integrated with the existing processor pipeline system:

```python
# Create processor template
template = await service.create_processor_template(
    sandbox_id, 
    "data_processor"
)

# Modify template and test
modified_code = template.replace(
    "# Add your transformation logic here",
    "return {'transformed': True, 'data': data}"
)

# Test the processor
result = await service.execute_code(sandbox_id, modified_code)
```

## Troubleshooting

### Common Issues

1. **Memory Limit Exceeded**
   - Reduce batch sizes
   - Use generators instead of lists
   - Clean up large objects

2. **Execution Timeout**
   - Optimize algorithms
   - Use async/await properly
   - Break large tasks into smaller chunks

3. **Database Query Errors**
   - Check SQL syntax
   - Use proper parameter binding
   - Verify table names and permissions

4. **Import Errors**
   - Check allowed modules list
   - Use alternative approaches for blocked modules
   - Request additional modules if needed

### Debug Steps

1. Enable debugging: `config['enable_debugging'] = True`
2. Use debug functions: `debug("message", "INFO")`
3. Inspect variables: `inspect_var("name", value)`
4. Check execution history: `get_execution_history()`
5. Review sandbox state: `get_sandbox_state()`

## Examples and Templates

See the `/sandbox/{sandbox_id}/help/examples` endpoint for more comprehensive examples and templates for common use cases.

## API Reference

Complete API documentation is available at `/docs` when running the server.

## Support

For issues or questions about the sandbox environment, check the logs and debug information provided by the sandbox service. 