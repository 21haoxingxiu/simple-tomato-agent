## Context

AgentStudio currently uses environment variables for model configuration (`OPENAI_API_KEY`, `EMBEDDING_PROVIDER`, etc.). This approach is:
- Not user-friendly for multi-provider scenarios
- Difficult to manage in production
- Lacks runtime configurability

RAGFlow provides a comprehensive model factory system with JSON-based configuration, supporting 30+ providers with multiple model types. We should adopt similar patterns.

**Current State:**
- `llm.py`: Single OpenAI-compatible LLM factory
- `rag/embeddings.py`: OpenAI + basic HuggingFace support
- No rerank model abstraction
- No model management API

**Stakeholders:**
- DevOps: Need to configure multiple providers
- Developers: Need to switch models easily
- End users: May want to select models per workspace

## Goals / Non-Goals

**Goals:**
- Implement model factory pattern with JSON configuration
- Support 5+ embedding providers (OpenAI, ZhipuAI, DashScope, Ollama, Voyage)
- Support 5+ LLM providers (OpenAI, DeepSeek, ZhipuAI, Moonshot, Mistral)
- Add rerank model abstraction with multiple providers
- Provide model management API for CRUD operations
- Maintain backward compatibility with environment variables

**Non-Goals:**
- Vision/multimodal model support (future phase)
- Model billing/usage tracking
- Custom model fine-tuning integration
- Model selection per user (only per workspace/global)

## Decisions

### D1: JSON-Based Model Configuration

**Decision:** Use JSON configuration files for model definitions, similar to RAGFlow's `llm_factories.json`.

**Rationale:**
- Easy to extend with new providers
- Can be loaded at runtime without code changes
- Clear separation of configuration and code
- RAGFlow has proven this pattern works

**Structure:**
```
conf/
  models/
    openai.json
    deepseek.json
    zhipuai.json
    ...
  model_factories.json  # Aggregated factory config
```

### D2: Model Factory Pattern

**Decision:** Implement abstract base classes for each model type with provider-specific implementations.

```python
class BaseEmbeddingModel(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    
    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...

class OpenAIEmbedding(BaseEmbeddingModel): ...
class ZhipuAIEmbedding(BaseEmbeddingModel): ...
class DashScopeEmbedding(BaseEmbeddingModel): ...
```

**Rationale:**
- Consistent interface across providers
- Easy to add new providers
- Type-safe with Pydantic schemas

### D3: Environment Variable Fallback

**Decision:** Maintain backward compatibility - environment variables act as defaults when JSON config is missing.

**Rationale:**
- Existing deployments won't break
- Simple development setup still works
- Gradual migration path

### D4: Database Storage for User Configurations

**Decision:** Store user-configured model credentials in database (encrypted), not in JSON files.

**Rationale:**
- JSON files are for default model definitions
- User credentials need secure storage
- Per-workspace model settings possible

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Provider SDK conflicts | Use optional dependencies, lazy imports |
| Credential exposure | Encrypt API keys in database, use env vars for defaults |
| Configuration complexity | Provide sensible defaults, UI for configuration |
| Breaking existing deployments | Environment variables still work as fallback |

## Migration Plan

### Phase 1: Core Model Factory
1. Create `models/` package with base classes
2. Implement OpenAI, ZhipuAI, DeepSeek providers
3. Add JSON configuration loading
4. Update `llm.py` and `embeddings.py` to use factory

### Phase 2: Additional Providers
1. Add DashScope, Ollama, Voyage embeddings
2. Add Moonshot, MiniMax, Mistral LLMs
3. Implement rerank model abstraction

### Phase 3: Model Management API
1. Add model configuration database model
2. Implement CRUD endpoints
3. Add model test endpoint

### Phase 4: Frontend (Optional)
1. Model settings page
2. Model selection in workspace settings

## Open Questions

1. Should we support local models via Ollama in Phase 1?
   - **Recommendation:** Yes, Ollama is simple to integrate

2. How to handle model-specific features (thinking mode, reasoning tokens)?
   - **Recommendation:** Add optional `extra_params` field in model config

3. Should model configurations be per-workspace or global?
   - **Recommendation:** Global defaults, workspace overrides (Phase 2)
