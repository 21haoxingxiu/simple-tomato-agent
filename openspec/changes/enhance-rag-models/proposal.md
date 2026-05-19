## Why

The current RAG implementation has limited model provider support - only OpenAI-compatible endpoints and basic HuggingFace embeddings. Users need to configure models via environment variables without a centralized management system. Following RAGFlow's patterns, we should support multiple LLM/embedding/rerank providers with a configurable model factory system.

## What Changes

### Model Provider System
- Add configurable model factory supporting 10+ providers (OpenAI, DeepSeek, ZhipuAI, Moonshot, Ollama, etc.)
- Support multiple model types: chat, embedding, rerank, TTS, STT
- Model configuration via JSON files (like RAGFlow's `llm_factories.json`)

### Embedding Models
- Add providers: ZhipuAI, DashScope (Alibaba), Ollama, Voyage, Jina
- Support model-specific parameters (dimensions, batch size)

### LLM Models
- Add providers: DeepSeek, ZhipuAI, Moonshot, MiniMax, Mistral, SiliconFlow
- Support provider-specific features (thinking mode, vision)

### Rerank Models
- Add proper rerank model abstractions
- Support Jina, Cohere, BGE rerankers

### Model Management API
- CRUD endpoints for model configurations
- List available models per provider
- Test model connectivity

## Capabilities

### New Capabilities
- `model-factory`: Configurable model provider system with JSON-based configuration
- `model-management-api`: REST API for managing model configurations
- `multi-provider-embeddings`: Support for multiple embedding providers (ZhipuAI, DashScope, Ollama, Voyage, Jina)
- `multi-provider-llm`: Support for multiple LLM providers (DeepSeek, ZhipuAI, Moonshot, MiniMax, Mistral)

### Modified Capabilities
- `knowledge-base`: RAG pipeline will use the new model factory for embeddings
- `conversation`: Chat will use the new model factory for LLM selection

## Impact

### Backend (Agent - Python)
- New `models/` directory with provider implementations
- New `conf/models/` directory with model configuration JSON files
- New router for model management API
- Updated `rag/embeddings.py` to use model factory
- Updated `llm.py` to use model factory

### Frontend (Next.js)
- New model management page (optional)
- Model selection dropdowns in settings

### Dependencies
- Add provider-specific SDKs: `zhipuai`, `dashscope`, `voyageai`, `cohere`, etc.
