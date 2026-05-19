## ADDED Requirements

### Requirement: OpenAI LLM Support

The system SHALL support OpenAI chat models with full API compatibility.

#### Scenario: Use gpt-4o
- **WHEN** OpenAI LLM is configured with model "gpt-4o"
- **THEN** the system supports 128k context
- **AND** supports function calling and vision

#### Scenario: Use gpt-4o-mini
- **WHEN** OpenAI LLM is configured with model "gpt-4o-mini"
- **THEN** the system provides cost-effective chat completions

### Requirement: DeepSeek LLM Support

The system SHALL support DeepSeek chat models.

#### Scenario: Use deepseek-chat
- **WHEN** DeepSeek LLM is configured
- **THEN** the system supports DeepSeek API
- **AND** requires DEEPSEEK_API_KEY

#### Scenario: Use deepseek-reasoner
- **WHEN** DeepSeek reasoner model is selected
- **THEN** the system supports thinking mode
- **AND** returns reasoning tokens in response

### Requirement: ZhipuAI LLM Support

The system SHALL support ZhipuAI (GLM) chat models.

#### Scenario: Use glm-4
- **WHEN** ZhipuAI LLM is configured with model "glm-4"
- **THEN** the system supports GLM API
- **AND** requires ZHIPUAI_API_KEY

#### Scenario: Use glm-4-flash
- **WHEN** ZhipuAI flash model is selected
- **THEN** the system provides fast, cost-effective completions

### Requirement: Moonshot LLM Support

The system SHALL support Moonshot (Kimi) chat models.

#### Scenario: Use moonshot-v1-8k
- **WHEN** Moonshot LLM is configured
- **THEN** the system supports Moonshot API
- **AND** requires MOONSHOT_API_KEY

### Requirement: Mistral LLM Support

The system SHALL support Mistral AI chat models.

#### Scenario: Use mistral-large-latest
- **WHEN** Mistral LLM is configured
- **THEN** the system supports Mistral API
- **AND** requires MISTRAL_API_KEY

### Requirement: Streaming Support

The system SHALL support streaming responses for all LLM providers.

#### Scenario: Stream OpenAI response
- **WHEN** streaming is enabled for OpenAI
- **THEN** the system returns tokens incrementally via SSE

#### Scenario: Stream DeepSeek response
- **WHEN** streaming is enabled for DeepSeek
- **THEN** the system returns tokens incrementally

### Requirement: Custom Base URL

The system SHALL allow custom base URLs for all providers.

#### Scenario: Use custom OpenAI-compatible endpoint
- **WHEN** provider is configured with custom base URL
- **THEN** the system sends requests to the custom endpoint
- **AND** maintains OpenAI API compatibility
