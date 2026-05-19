"""Model management API router."""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.factory import get_model_factory
from models.schemas import (
    ModelInfo,
    ModelTestRequest,
    ModelTestResponse,
    ProviderInfo,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["models"])


class CredentialsRequest(BaseModel):
    provider: str
    api_key: str
    base_url: str | None = None


class DefaultsRequest(BaseModel):
    chat_model: str | None = None
    embedding_model: str | None = None
    rerank_model: str | None = None


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    """List all available model providers."""
    factory = get_model_factory()
    providers = factory.list_providers()
    result = []
    for p in providers:
        configured = factory.get_credential(p.name) is not None
        result.append(
            ProviderInfo(
                name=p.name,
                provider_class=p.provider_class,
                supports=p.supports,
                model_count=len(p.models),
                configured=configured,
            )
        )
    return result


@router.get("/providers/{provider}/models", response_model=list[ModelInfo])
async def list_models(provider: str):
    """List all models for a specific provider."""
    factory = get_model_factory()
    models = factory.list_models(provider)
    if models is None:
        raise HTTPException(404, f"Provider '{provider}' not found")
    return [
        ModelInfo(
            name=m.name,
            max_tokens=m.max_tokens,
            model_types=m.model_types,
            extra_params=m.extra_params,
        )
        for m in models
    ]


@router.get("/providers/{provider}/models/{model}", response_model=ModelInfo)
async def get_model(provider: str, model: str):
    """Get details for a specific model."""
    factory = get_model_factory()
    models = factory.list_models(provider)
    if models is None:
        raise HTTPException(404, f"Provider '{provider}' not found")
    for m in models:
        if m.name == model:
            return ModelInfo(
                name=m.name,
                max_tokens=m.max_tokens,
                model_types=m.model_types,
                extra_params=m.extra_params,
            )
    raise HTTPException(404, f"Model '{model}' not found in provider '{provider}'")


@router.post("/test", response_model=ModelTestResponse)
async def test_model(request: ModelTestRequest):
    """Test connectivity to a model provider."""
    factory = get_model_factory()

    # Use provided credentials or fallback to stored/env
    api_key = request.api_key or factory.get_credential(request.provider)

    if not api_key:
        return ModelTestResponse(
            success=False,
            latency_ms=0,
            error=f"No API key configured for provider '{request.provider}'",
        )

    start = time.time()
    try:
        if request.model_type == "embedding":
            model = factory.get_embedding_model(
                provider=request.provider,
                model=request.model,
                api_key=api_key,  # Pass the API key directly
            )
            # Test with a simple embedding
            model.embed_query("test")
        elif request.model_type == "chat":
            model = factory.get_chat_model(
                provider=request.provider,
                model=request.model,
                api_key=api_key,  # Pass the API key directly
            )
            # Test with a simple invocation
            model.invoke([{"role": "user", "content": "hi"}])
        elif request.model_type == "rerank":
            model = factory.get_rerank_model(
                provider=request.provider,
                model=request.model,
                api_key=api_key,  # Pass the API key directly
            )
            model.rerank("test", [{"content": "test", "chunk_id": "1"}])
        else:
            raise HTTPException(400, f"Unknown model type: {request.model_type}")

        latency = int((time.time() - start) * 1000)
        return ModelTestResponse(
            success=True,
            latency_ms=latency,
            model_info={"provider": request.provider, "model": request.model},
        )
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return ModelTestResponse(
            success=False,
            latency_ms=latency,
            error=str(e),
        )


@router.post("/credentials")
async def save_credentials(request: CredentialsRequest):
    """Save API credentials for a provider."""
    factory = get_model_factory()
    factory.set_credential(request.provider, request.api_key)
    return {"ok": True, "provider": request.provider}


@router.patch("/defaults")
async def set_defaults(request: DefaultsRequest):
    """Set default models for each type."""
    # For now, just acknowledge - could store in database later
    return {
        "ok": True,
        "defaults": {
            "chat_model": request.chat_model,
            "embedding_model": request.embedding_model,
            "rerank_model": request.rerank_model,
        },
    }
