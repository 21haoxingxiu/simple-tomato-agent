## ADDED Requirements

### Requirement: Space Context Header

The system SHALL require `X-Space-ID` header for all resource-related API requests.

#### Scenario: Request with valid space header
- **WHEN** API request includes valid `X-Space-ID` header
- **THEN** system processes the request in the context of that space

#### Scenario: Request without space header
- **WHEN** API request lacks `X-Space-ID` header
- **THEN** system returns 400 BAD REQUEST with error message "X-Space-ID header is required"

#### Scenario: Request with invalid space ID
- **WHEN** API request includes non-existent space ID in `X-Space-ID` header
- **THEN** system returns 404 NOT FOUND with error message "Space not found"

### Requirement: Knowledge Base Space Isolation

The system SHALL isolate knowledge bases by space.

#### Scenario: Create knowledge base in space
- **WHEN** user creates a knowledge base with `X-Space-ID: space-1`
- **THEN** the knowledge base is associated with space-1
- **AND** the knowledge base is NOT visible in other spaces

#### Scenario: List knowledge bases in space
- **WHEN** user lists knowledge bases with `X-Space-ID: space-1`
- **THEN** system returns only knowledge bases belonging to space-1

#### Scenario: Access knowledge base from different space
- **WHEN** user tries to access knowledge base from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Conversation Space Isolation

The system SHALL isolate conversations by space.

#### Scenario: Create conversation in space
- **WHEN** user sends a chat message with `X-Space-ID: space-1`
- **THEN** the conversation is associated with space-1
- **AND** the conversation is NOT visible in other spaces

#### Scenario: List conversations in space
- **WHEN** user lists conversations with `X-Space-ID: space-1`
- **THEN** system returns only conversations belonging to space-1

#### Scenario: Continue conversation from different space
- **WHEN** user tries to continue a conversation from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Evaluation Space Isolation

The system SHALL isolate evaluation cases by space.

#### Scenario: Create evaluation case in space
- **WHEN** user creates an evaluation case with `X-Space-ID: space-1`
- **THEN** the evaluation case is associated with space-1
- **AND** the evaluation case is NOT visible in other spaces

#### Scenario: List evaluation cases in space
- **WHEN** user lists evaluation cases with `X-Space-ID: space-1`
- **THEN** system returns only evaluation cases belonging to space-1

#### Scenario: Run evaluation from different space
- **WHEN** user tries to run an evaluation case from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Vector Store Space Filtering

The system SHALL filter vector store queries by space.

#### Scenario: Vector search respects space
- **WHEN** RAG retrieval is performed with `X-Space-ID: space-1`
- **THEN** only vectors with `space_id=space-1` metadata are searched

#### Scenario: Document ingestion tags space
- **WHEN** document is uploaded to knowledge base in space-1
- **THEN** vectors are stored with `space_id=space-1` metadata

### Requirement: Space Deletion Cascades

The system SHALL cascade delete resources when a space is deleted.

#### Scenario: Delete space removes all resources
- **WHEN** a space is permanently deleted
- **THEN** all knowledge bases, conversations, and evaluation cases in that space are deleted
- **AND** all vectors associated with that space are deleted
