# bash apps/llm/tests/scripts.sh

# 1. Health Check
curl -X GET http://localhost:8001/health

# 2. Extract text from document (no DB save)
curl -X POST http://localhost:8001/api/v1/documents/extract-text -F "file=@/Users/tatoaoliang/Downloads/金蝶/合同/第一编/1-1 买卖合同（通用版）.pdf"

# 3. Analyze document structure
curl -X POST http://localhost:8001/api/v1/documents/analyze -F "file=@/Users/tatoaoliang/Downloads/金蝶/合同/第一编/1-1 买卖合同（通用版）.pdf"

# 4a. Process document using DIRECT FILE UPLOAD (documents endpoint)
echo "=== Direct file upload processing ==="
curl -X POST http://localhost:8001/api/v1/documents/process \
  -F "file=@/Users/tatoaoliang/Downloads/金蝶/合同/第一编/1-1 买卖合同（通用版）.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"

# 4b. Process document using PROCESSOR PIPELINE (requires file_hash - use this for advanced processing)
echo "=== Processor pipeline processing (requires file_hash) ==="
# Note: This endpoint expects JSON data, not form data
# You need to first upload the file to get a hash, then use this endpoint
# Example JSON request (replace with actual values):
# curl -X POST http://localhost:8001/api/v1/processors/process \
#   -H "Content-Type: application/json" \
#   -d '{
#     "file_hash": "your_file_hash_here",
#     "user_id": 1,
#     "filename": "1-1 买卖合同（通用版）.pdf",
#     "pipeline": [
#       {
#         "processor_id": "fixed_size_chunker",
#         "config": {
#           "chunk_size": 1000,
#           "overlap": 200
#         }
#       }
#     ]
#   }'

# 5. Get supported formats
curl -X GET http://localhost:8001/api/v1/documents/supported-formats