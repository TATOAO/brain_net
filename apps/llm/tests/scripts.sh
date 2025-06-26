# bash apps/llm/tests/scripts.sh

# 1. Health Check
curl -X GET http://localhost:8001/health

# # 2. Extract text from document (no DB save)
curl -X POST http://localhost:8001/api/v1/documents/extract-text -F "file=@/Users/tatoaoliang/Downloads/金蝶/合同/第一编/1-1 买卖合同（通用版）.pdf"

# # 3. Analyze document structure
# POST http://localhost:8001/api/v1/documents/analyze  
# - Form-data: file: [your_document.pdf]

# # 4. Process document to chunks (temporary processing)
# POST http://localhost:8001/api/v1/documents/process
# - Form-data: file: [your_document.pdf]
# - Form-data: chunk_size: 1000
# - Form-data: chunk_overlap: 200

# # 5. Get supported formats
# GET http://localhost:8001/api/v1/documents/supported-formats