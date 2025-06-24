"""
Example service demonstrating OpenTelemetry custom instrumentation for LLM operations
"""

import time
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from app.core.telemetry import get_tracer, get_meter

logger = logging.getLogger(__name__)

# Get tracer and meter instances
tracer = get_tracer()
meter = get_meter()

# Create custom metrics for LLM operations
llm_requests_counter = meter.create_counter(
    name="llm_requests_total",
    description="Total number of LLM requests processed",
    unit="requests"
)

llm_request_duration = meter.create_histogram(
    name="llm_request_duration_seconds",
    description="LLM request processing duration",
    unit="seconds"
)

token_usage_counter = meter.create_counter(
    name="llm_tokens_used_total",
    description="Total tokens consumed by LLM",
    unit="tokens"
)

embedding_requests_counter = meter.create_counter(
    name="embedding_requests_total",
    description="Total embedding requests processed",
    unit="requests"
)

vector_search_counter = meter.create_counter(
    name="vector_searches_total",
    description="Total vector searches performed",
    unit="searches"
)

rag_pipeline_duration = meter.create_histogram(
    name="rag_pipeline_duration_seconds",
    description="RAG pipeline processing duration",
    unit="seconds"
)


class LLMTelemetryService:
    """Service demonstrating OpenTelemetry usage patterns for LLM operations."""
    
    def __init__(self):
        self.tracer = tracer
        self.meter = meter
    
    @asynccontextmanager
    async def trace_llm_operation(self, operation_name: str, **attributes):
        """Context manager for tracing LLM operations."""
        with self.tracer.start_as_current_span(operation_name) as span:
            start_time = time.time()
            try:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(f"llm.{key}", str(value))
                
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record exception and mark as error
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                llm_request_duration.record(duration, {
                    "operation": operation_name,
                    "status": "success" if span.status.status_code == StatusCode.OK else "error"
                })
    
    async def process_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Example: Chat completion with comprehensive tracing."""
        async with self.trace_llm_operation(
            "chat_completion",
            model=model,
            message_count=len(messages),
            user_id=user_id or "anonymous"
        ) as span:
            # Increment request counter
            llm_requests_counter.add(1, {
                "model": model,
                "operation": "chat_completion"
            })
            
            # Calculate input tokens (simplified)
            input_text = " ".join([msg.get("content", "") for msg in messages])
            input_tokens = len(input_text.split())
            
            span.set_attributes({
                "llm.input_tokens": input_tokens,
                "llm.temperature": 0.7,
                "llm.max_tokens": 2048
            })
            
            # Simulate LLM API call
            await self._simulate_llm_call(1.5)
            
            # Mock response
            response_text = f"This is a simulated response for {len(messages)} messages"
            output_tokens = len(response_text.split())
            total_tokens = input_tokens + output_tokens
            
            # Record token usage
            token_usage_counter.add(total_tokens, {
                "model": model,
                "type": "total"
            })
            token_usage_counter.add(input_tokens, {
                "model": model,
                "type": "input"
            })
            token_usage_counter.add(output_tokens, {
                "model": model,
                "type": "output"
            })
            
            span.set_attributes({
                "llm.output_tokens": output_tokens,
                "llm.total_tokens": total_tokens,
                "llm.finish_reason": "stop"
            })
            
            span.add_event("Chat completion successful", {
                "response_length": len(response_text)
            })
            
            return {
                "response": response_text,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "model": model
            }
    
    async def process_rag_query(
        self, 
        query: str, 
        collection_name: str,
        top_k: int = 5,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Example: RAG pipeline with detailed tracing."""
        async with self.trace_llm_operation(
            "rag_query",
            query_length=len(query),
            collection=collection_name,
            top_k=top_k,
            user_id=user_id or "anonymous"
        ) as span:
            start_time = time.time()
            
            try:
                # Step 1: Generate embeddings
                embeddings = await self._generate_embeddings(query)
                
                # Step 2: Vector search
                search_results = await self._vector_search(embeddings, collection_name, top_k)
                
                # Step 3: Retrieve context
                context = await self._retrieve_context(search_results)
                
                # Step 4: Generate response
                response = await self._generate_rag_response(query, context)
                
                # Record overall pipeline duration
                pipeline_duration = time.time() - start_time
                rag_pipeline_duration.record(pipeline_duration, {
                    "collection": collection_name,
                    "context_sources": len(search_results)
                })
                
                span.add_event("RAG pipeline completed", {
                    "context_sources": len(search_results),
                    "response_length": len(response)
                })
                
                return {
                    "query": query,
                    "response": response,
                    "sources": search_results,
                    "context_length": len(context)
                }
                
            except Exception as e:
                span.add_event("RAG pipeline failed", {"error": str(e)})
                raise
    
    async def _generate_embeddings(self, text: str) -> List[float]:
        """Generate embeddings with tracing."""
        with self.tracer.start_as_current_span("generate_embeddings") as span:
            span.set_attributes({
                "embedding.model": "text-embedding-ada-002",
                "embedding.input_length": len(text),
                "embedding.input_tokens": len(text.split())
            })
            
            # Increment embedding request counter
            embedding_requests_counter.add(1, {
                "model": "text-embedding-ada-002"
            })
            
            # Simulate embedding generation
            await self._simulate_llm_call(0.3)
            
            # Mock embeddings (1536 dimensions for ada-002)
            embeddings = [0.1] * 1536
            
            span.set_attributes({
                "embedding.dimensions": len(embeddings)
            })
            
            span.add_event("Embeddings generated successfully")
            return embeddings
    
    async def _vector_search(
        self, 
        embeddings: List[float], 
        collection_name: str, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Perform vector search with tracing."""
        with self.tracer.start_as_current_span("vector_search") as span:
            span.set_attributes({
                "vector.collection": collection_name,
                "vector.dimensions": len(embeddings),
                "vector.top_k": top_k,
                "vector.similarity_metric": "cosine"
            })
            
            # Increment vector search counter
            vector_search_counter.add(1, {
                "collection": collection_name,
                "search_type": "similarity"
            })
            
            # Simulate vector search
            await self._simulate_async_work(0.2)
            
            # Mock search results
            results = [
                {
                    "id": f"doc_{i}",
                    "score": 0.9 - (i * 0.1),
                    "metadata": {"source": f"document_{i}.pdf"},
                    "content": f"This is relevant content from document {i}"
                }
                for i in range(min(top_k, 3))
            ]
            
            span.set_attributes({
                "vector.results_found": len(results),
                "vector.max_score": max([r["score"] for r in results]) if results else 0,
                "vector.min_score": min([r["score"] for r in results]) if results else 0
            })
            
            span.add_event("Vector search completed", {
                "results_count": len(results)
            })
            
            return results
    
    async def _retrieve_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Retrieve and format context from search results."""
        with self.tracer.start_as_current_span("retrieve_context") as span:
            span.set_attributes({
                "context.source_count": len(search_results)
            })
            
            # Simulate context retrieval
            await self._simulate_async_work(0.1)
            
            context_parts = [result["content"] for result in search_results]
            context = "\n\n".join(context_parts)
            
            span.set_attributes({
                "context.length": len(context),
                "context.token_estimate": len(context.split())
            })
            
            span.add_event("Context retrieved and formatted")
            return context
    
    async def _generate_rag_response(self, query: str, context: str) -> str:
        """Generate RAG response with tracing."""
        with self.tracer.start_as_current_span("generate_rag_response") as span:
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
            
            span.set_attributes({
                "rag.query_length": len(query),
                "rag.context_length": len(context),
                "rag.prompt_length": len(prompt),
                "rag.model": "gpt-3.5-turbo"
            })
            
            # Simulate LLM call for response generation
            await self._simulate_llm_call(2.0)
            
            response = f"Based on the provided context, here's the answer to your query: {query[:50]}..."
            
            span.set_attributes({
                "rag.response_length": len(response)
            })
            
            span.add_event("RAG response generated successfully")
            return response
    
    async def _simulate_llm_call(self, duration: float):
        """Simulate LLM API call with realistic delay."""
        import asyncio
        await asyncio.sleep(duration)
    
    async def _simulate_async_work(self, duration: float):
        """Simulate async work for demo purposes."""
        import asyncio
        await asyncio.sleep(duration)
    
    def record_agent_metrics(
        self, 
        agent_name: str, 
        task_type: str, 
        duration: float, 
        success: bool,
        iterations: int
    ):
        """Record metrics for agent operations."""
        agent_counter = meter.create_counter(
            name="agent_tasks_total",
            description="Total agent tasks executed",
            unit="tasks"
        )
        
        agent_duration = meter.create_histogram(
            name="agent_task_duration_seconds",
            description="Agent task execution duration",
            unit="seconds"
        )
        
        agent_counter.add(1, {
            "agent": agent_name,
            "task_type": task_type,
            "status": "success" if success else "failure"
        })
        
        agent_duration.record(duration, {
            "agent": agent_name,
            "task_type": task_type,
            "iterations": str(iterations)
        })


# Global service instance
llm_telemetry_service = LLMTelemetryService() 