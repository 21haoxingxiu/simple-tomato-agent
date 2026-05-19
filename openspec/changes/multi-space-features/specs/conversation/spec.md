## MODIFIED Requirements

### Requirement: Create Conversation

The system SHALL create conversations scoped to a specific space.

#### Scenario: Start new conversation in space
- **WHEN** user sends first message with `X-Space-ID: space-1`
- **THEN** system creates a new conversation in space-1
- **AND** system returns conversation ID

#### Scenario: Conversation without space
- **WHEN** user sends message without `X-Space-ID` header
- **THEN** system returns 400 BAD REQUEST

### Requirement: Stream Chat Response

The system SHALL stream chat responses for conversations within the same space.

#### Scenario: Stream response in same space
- **WHEN** user sends message to existing conversation with matching `X-Space-ID`
- **THEN** system streams response via SSE
- **AND** response includes retrieved chunks from space-scoped knowledge bases

#### Scenario: Stream response to conversation in different space
- **WHEN** user sends message to conversation from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: List Conversations

The system SHALL return only conversations belonging to the current space.

#### Scenario: List conversations in space
- **WHEN** user requests conversation list with `X-Space-ID: space-1`
- **THEN** system returns all conversations in space-1
- **AND** conversations from other spaces are NOT included

### Requirement: Get Conversation Messages

The system SHALL return messages for a conversation only within the same space.

#### Scenario: Get messages in same space
- **WHEN** user requests messages for conversation with matching `X-Space-ID`
- **THEN** system returns all messages in the conversation

#### Scenario: Get messages from different space
- **WHEN** user requests messages for conversation in space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Delete Conversation

The system SHALL allow deleting conversations only within the same space.

#### Scenario: Delete conversation in same space
- **WHEN** user deletes conversation with matching space context
- **THEN** system deletes the conversation and all messages

#### Scenario: Delete conversation from different space
- **WHEN** user tries to delete conversation from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: RAG Context Space Scoping

The system SHALL retrieve context only from knowledge bases in the same space as the conversation.

#### Scenario: RAG retrieves from space knowledge bases
- **WHEN** conversation is in space-1
- **THEN** RAG retrieval queries only knowledge bases in space-1
- **AND** knowledge bases from other spaces are NOT queried
