## 1. Project Structure & Configuration

- [x] 1.1 Create `agent/models/` package directory
- [x] 1.2 Create `agent/conf/models/` directory for JSON configs
- [ ] 1.3 Create `agent/conf/model_factories.json` main configuration file (optional - using individual files)
- [x] 1.4 Add provider SDK dependencies to `requirements.txt` (zhipuai, dashscope, voyageai, cohere)

## 2. Base Model Classes

- [x] 2.1 Create `agent/models/base.py` with abstract base classes
- [x] 2.2 Define `BaseEmbeddingModel` abstract class
- [x] 2.3 Define `BaseChatModel` abstract class
- [x] 2.4 Define `BaseRerankModel` abstract class
- [x] 2.5 Create `agent/models/schemas.py` with Pydantic models for configuration

## 3. Model Factory Implementation

- [x] 3.1 Create `agent/models/factory.py` with `ModelFactory` class
- [x] 3.2 Implement configuration loading from JSON files
- [x] 3.3 Implement provider registration mechanism
- [x] 3.4 Implement `get_embedding_model()` factory method
- [x] 3.5 Implement `get_chat_model()` factory method
- [x] 3.6 Implement `get_rerank_model()` factory method
- [x] 3.7 Add environment variable fallback logic

## 4. Embedding Model Providers

- [x] 4.1 Create `agent/models/embeddings/__init__.py`
- [x] 4.2 Implement `OpenAIEmbeddingModel` in `embeddings/openai.py`
- [x] 4.3 Implement `ZhipuAIEmbeddingModel` in `embeddings/zhipuai.py`
- [x] 4.4 Implement `DashScopeEmbeddingModel` in `embeddings/dashscope.py`
- [x] 4.5 Implement `OllamaEmbeddingModel` in `embeddings/ollama.py`
- [x] 4.6 Implement `VoyageEmbeddingModel` in `embeddings/voyage.py`
- [x] 4.7 Implement `HuggingFaceEmbeddingModel` in `embeddings/huggingface.py`

## 5. LLM Providers

- [x] 5.1 Create `agent/models/llm/__init__.py`
- [x] 5.2 Implement `OpenAIChatModel` in `llm/openai.py`
- [x] 5.3 Implement `DeepSeekChatModel` in `llm/deepseek.py`
- [x] 5.4 Implement `ZhipuAIChatModel` in `llm/zhipuai.py`
- [x] 5.5 Implement `MoonshotChatModel` in `llm/moonshot.py`
- [x] 5.6 Implement `MistralChatModel` in `llm/mistral.py`
- [x] 5.7 Implement `OllamaChatModel` in `llm/ollama.py`

## 6. Rerank Model Providers

- [x] 6.1 Create `agent/models/rerank/__init__.py`
- [x] 6.2 Implement `BaseRerankModel` with common interface
- [x] 6.3 Implement `JinaRerankModel` in `rerank/jina.py`
- [x] 6.4 Implement `CohereRerankModel` in `rerank/cohere.py`
- [ ] 6.5 Update existing `rag/reranker.py` to use factory (optional enhancement)

## 7. JSON Configuration Files

- [x] 7.1 Create `conf/models/openai.json` with OpenAI model definitions
- [x] 7.2 Create `conf/models/deepseek.json` with DeepSeek model definitions
- [x] 7.3 Create `conf/models/zhipuai.json` with ZhipuAI model definitions
- [x] 7.4 Create `conf/models/moonshot.json` with Moonshot model definitions
- [x] 7.5 Create `conf/models/mistral.json` with Mistral model definitions
- [x] 7.6 Create `conf/models/ollama.json` with Ollama model definitions
- [x] 7.7 Create `conf/models/jina.json` with Jina model definitions

## 8. Model Management API

- [x] 8.1 Create `agent/routers/models.py` with model management endpoints
- [x] 8.2 Implement `GET /api/models/providers` - list providers
- [x] 8.3 Implement `GET /api/models/providers/{provider}/models` - list models
- [x] 8.4 Implement `GET /api/models/providers/{provider}/models/{model}` - get model config
- [x] 8.5 Implement `POST /api/models/test` - test model connectivity
- [x] 8.6 Implement `POST /api/models/credentials` - save credentials
- [x] 8.7 Implement `PATCH /api/models/defaults` - set default models
- [x] 8.8 Register models router in `main.py`

## 9. Database Schema for Credentials

- [ ] 9.1 Create `ModelCredential` database model in `db/models.py` (future enhancement)
- [ ] 9.2 Add Alembic migration for model credentials table (future enhancement)
- [ ] 9.3 Implement credential encryption/decryption utilities (future enhancement)

## 10. Update Existing Code

- [ ] 10.1 Update `agent/llm.py` to use `ModelFactory` (backward compatible - existing code works)
- [ ] 10.2 Update `agent/rag/embeddings.py` to use `ModelFactory` (backward compatible - existing code works)
- [ ] 10.3 Update `agent/rag/pipeline.py` to use new embedding factory (optional)
- [ ] 10.4 Update `agent/agents/chat_agent.py` to use new LLM factory (optional)

## 11. Testing

- [ ] 11.1 Add unit tests for model factory
- [ ] 11.2 Add unit tests for each embedding provider
- [ ] 11.3 Add unit tests for each LLM provider
- [ ] 11.4 Add integration tests for model management API

## 12. Documentation

- [ ] 12.1 Update README with model configuration instructions
- [ ] 12.2 Add API documentation for model endpoints
- [ ] 12.3 Create example configuration files
