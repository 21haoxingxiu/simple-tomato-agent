## ADDED Requirements

### Requirement: Load Model Configuration from JSON

The system SHALL load model provider configurations from JSON files at startup.

#### Scenario: Load default model configurations
- **WHEN** the application starts
- **THEN** the system loads model configurations from `conf/models/*.json`
- **AND** the configurations are available for model instantiation

#### Scenario: Missing configuration file
- **WHEN** a model configuration file is missing
- **THEN** the system continues with environment variable fallback
- **AND** a warning is logged

### Requirement: Model Factory Creates Provider Instances

The system SHALL provide a model factory that creates provider-specific model instances based on configuration.

#### Scenario: Create embedding model by provider
- **WHEN** user requests an embedding model for provider "zhipuai"
- **THEN** the factory returns a ZhipuAIEmbedding instance
- **AND** the instance is configured with the correct API key and model name

#### Scenario: Create LLM by provider
- **WHEN** user requests a chat model for provider "deepseek"
- **THEN** the factory returns a DeepSeekChatModel instance
- **AND** the instance is configured correctly

#### Scenario: Unknown provider fallback
- **WHEN** user requests a model for unknown provider "unknown-provider"
- **THEN** the system returns an error indicating the provider is not supported
- **AND** lists available providers

### Requirement: Environment Variable Fallback

The system SHALL fall back to environment variables when JSON configuration is not available.

#### Scenario: No JSON config uses env vars
- **WHEN** no model JSON configuration exists
- **THEN** the system uses `OPENAI_API_KEY`, `OPENAI_BASE_URL`, etc.
- **AND** creates an OpenAI-compatible model

### Requirement: Provider Registration

The system SHALL allow registering new model providers dynamically.

#### Scenario: Register custom provider
- **WHEN** a custom provider is registered with the factory
- **THEN** the provider is available for model creation
- **AND** the provider appears in the provider list
