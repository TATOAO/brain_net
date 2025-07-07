from typing import List, AsyncGenerator
import json
import httpx
from pydantic import FilePath
from processor_pipeline import AsyncProcessor
from app.core.config import settings


class ChunkingProcessor(AsyncProcessor):
    """
    Chunking processor is used to chunk the document into smaller chunks.
    It is used to create the context for the LLM to use.
    It is used to create the context for the LLM to use.
    """
    meta = {
        "name": "chunking_processor",
        "input_type": FilePath,
        "output_type": List[str],
    }

    async def process(self, file_path: str) -> AsyncGenerator[str, None]:
        print(f"🚀 Starting document chunking for: {file_path}")
        print(f"📡 Using endpoint: {settings.COMPACT_LLM_URL}/doc_chunking/api/chunk-document-sse")
        
        with open(file_path, "rb") as f:
            files = {
                'file': (f.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            
            try:
                async with httpx.AsyncClient() as http_client:
                    print("🌐 Making HTTP request...")
                    async with http_client.stream(
                        'POST',
                        f'{settings.COMPACT_LLM_URL}/doc_chunking/api/chunk-document-sse',
                        files=files,
                        headers={'Accept': 'text/event-stream'},
                        timeout=30.0
                    ) as response:
                        print(f"📊 Response status: {response.status_code}")
                        print(f"📋 Response headers: {dict(response.headers)}")
                        
                        if response.status_code != 200:
                            print(f"❌ HTTP Error: {response.status_code}")
                            response_text = await response.aread()
                            print(f"Response body: {response_text}")
                            return
                        
                        print("✅ Starting SSE stream processing...")
                        line_count = 0
                        async for line in response.aiter_lines():
                            line_count += 1
                            if line_count % 10 == 0:
                                print(f"📊 Processed {line_count} lines so far...")
                            
                            if line:
                                line = line.strip()
                                print(f"📝 Raw line: {line}")
                                
                                if line.startswith('event:'):
                                    event_type = line.split(':', 1)[1].strip()
                                    print(f"🎯 Event type: {event_type}")
                                elif line.startswith('data:'):
                                    data_content = line.split(':', 1)[1].strip()
                                    print(f"📦 Data content: {data_content}")
                                    try:
                                        data = json.loads(data_content)
                                        print(f"✅ Parsed data: {data}")
                                        yield data
                                    except json.JSONDecodeError as e:
                                        print(f"❌ JSON decode error: {e}")
                                        print(f"Raw data: {data_content}")
                        
                        print(f"🏁 Stream ended. Total lines processed: {line_count}")
                        
            except httpx.RequestError as e:
                print(f"❌ HTTP Request error: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()


# python -m app.core.processor.chunking_processor
if __name__ == "__main__":
    import asyncio
    file_path = "/Users/tatoaoliang/Downloads/Work/doc_chunking/tests/test_data/1-1 买卖合同（通用版）.docx"
    async def main():
        async for chunk in ChunkingProcessor().process(file_path):
            print(chunk)
    asyncio.run(main())