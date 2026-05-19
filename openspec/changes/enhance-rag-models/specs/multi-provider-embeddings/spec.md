## ADDED Requirements

### Requirement: OpenAI Embeddings

The system SHALL support OpenAI embeddings with configurable models.

#### Scenario: Use text-embedding-3-small
- **WHEN** OpenAI embedding is configured with model "text-embedding-3-small"
- **THEN** the system generates 1536-dimensional embeddings
- **AND** supports the full OpenAI API parameters

#### Scenario: Use text-embedding-3-large
- **WHEN** OpenAI embedding is configured with model "text-embedding-3-large"
- **THEN** the system generates 3072-dimensional embeddings

### Requirement: ZhipuAI Embeddings

The system SHALL support ZhipuAI embedding models.

#### Scenario: Use embedding-3
- **WHEN** ZhipuAI embedding is configured with model "embedding-3"
- **THEN** the system generates embeddings using ZhipuAI API
- **AND** requires ZHIPUAI_API_KEY configuration

### Requirement: DashScope Embeddings

The system SHALL support Alibaba DashScope (Tongyi) embeddings.

#### Scenario: Use DashScope text-embedding
- **WHEN** DashScope embedding is configured
- **THEN** the system generates embeddings using DashScope API
- **AND** supports both CN and international endpoints

### Requirement: Ollama Embeddings

The system SHALL support local Ollama embeddings.

#### Scenario: Use local Ollama embedding
- **WHEN** Ollama embedding is configured with base URL "http://localhost:11434"
- **THEN** the system generates embeddings via Ollama API
- **AND** works without external API keys

### Requirement: Voyage Embeddings

The system SHALL support Voyage AI embeddings.

#### Scenario: Use voyage-3-large
- **WHEN** Voyage embedding is configured
- **THEN** the system generates embeddings using Voyage API
- **AND** requires VOYAGE_API_KEY

### Requirement: Embedding Dimension Configuration

The system SHALL allow specifying embedding dimensions where supported.

#### Scenario: Configure custom dimensions
- **WHEN** embedding model supports dimension parameter
- **THEN** user can specify desired output dimensions
- **AND** embeddings are truncated/padded accordingly
