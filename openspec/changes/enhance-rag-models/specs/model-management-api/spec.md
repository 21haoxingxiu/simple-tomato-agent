## ADDED Requirements

### Requirement: List Model Providers

The system SHALL provide an API endpoint to list all available model providers.

#### Scenario: List all providers
- **WHEN** user requests `GET /api/models/providers`
- **THEN** the system returns a list of all configured providers
- **AND** each provider includes name, supported model types, and available models

### Requirement: List Models by Provider

The system SHALL provide an API endpoint to list available models for a specific provider.

#### Scenario: List OpenAI models
- **WHEN** user requests `GET /api/models/providers/openai/models`
- **THEN** the system returns all configured OpenAI models
- **AND** each model includes name, max_tokens, model_type

### Requirement: Get Model Configuration

The system SHALL provide an API endpoint to get a specific model's configuration.

#### Scenario: Get model config
- **WHEN** user requests `GET /api/models/providers/openai/models/gpt-4o-mini`
- **THEN** the system returns the model's configuration
- **AND** includes all model parameters

### Requirement: Test Model Connectivity

The system SHALL provide an API endpoint to test if a model configuration works.

#### Scenario: Test successful connection
- **WHEN** user requests `POST /api/models/test` with provider and model
- **THEN** the system attempts to call the model
- **AND** returns success status with latency

#### Scenario: Test failed connection
- **WHEN** user requests `POST /api/models/test` with invalid credentials
- **THEN** the system returns failure status
- **AND** includes error message

### Requirement: Configure Model Credentials

The system SHALL allow storing model API keys securely.

#### Scenario: Save provider credentials
- **WHEN** user saves API key for a provider via `POST /api/models/credentials`
- **THEN** the system stores the credential securely (encrypted)
- **AND** subsequent model calls use the stored credential

#### Scenario: Update provider credentials
- **WHEN** user updates API key for existing provider
- **THEN** the system replaces the old credential
- **AND** model calls use the new credential

### Requirement: Set Default Model

The system SHALL allow setting default models for each model type.

#### Scenario: Set default chat model
- **WHEN** user sets default chat model via `PATCH /api/models/defaults`
- **THEN** all chat operations use the specified model by default

#### Scenario: Set default embedding model
- **WHEN** user sets default embedding model
- **THEN** all RAG operations use the specified embedding model
