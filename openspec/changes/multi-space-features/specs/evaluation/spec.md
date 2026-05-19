## MODIFIED Requirements

### Requirement: Create Evaluation Case

The system SHALL create evaluation cases scoped to a specific space.

#### Scenario: Create evaluation case in space
- **WHEN** user creates evaluation case with `X-Space-ID: space-1`
- **THEN** system creates evaluation case in space-1
- **AND** system returns evaluation case details

#### Scenario: Create evaluation case without space
- **WHEN** user creates evaluation case without `X-Space-ID` header
- **THEN** system returns 400 BAD REQUEST

### Requirement: List Evaluation Cases

The system SHALL return only evaluation cases belonging to the current space.

#### Scenario: List evaluation cases in space
- **WHEN** user requests evaluation case list with `X-Space-ID: space-1`
- **THEN** system returns all evaluation cases in space-1
- **AND** evaluation cases from other spaces are NOT included

### Requirement: Get Evaluation Case

The system SHALL return evaluation case details only if it belongs to the current space.

#### Scenario: Get evaluation case in same space
- **WHEN** user requests evaluation case with valid ID and matching `X-Space-ID`
- **THEN** system returns evaluation case details

#### Scenario: Get evaluation case from different space
- **WHEN** user requests evaluation case from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Update Evaluation Case

The system SHALL allow updating evaluation cases only within the same space.

#### Scenario: Update evaluation case in same space
- **WHEN** user updates evaluation case with matching space context
- **THEN** system updates the evaluation case
- **AND** system returns updated details

#### Scenario: Update evaluation case from different space
- **WHEN** user tries to update evaluation case from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Delete Evaluation Case

The system SHALL allow deleting evaluation cases only within the same space.

#### Scenario: Delete evaluation case in same space
- **WHEN** user deletes evaluation case with matching space context
- **THEN** system deletes the evaluation case

#### Scenario: Delete evaluation case from different space
- **WHEN** user tries to delete evaluation case from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Run Evaluation

The system SHALL run evaluations only within the same space.

#### Scenario: Run evaluation in same space
- **WHEN** user runs evaluation case with matching space context
- **THEN** system executes the evaluation
- **AND** system returns evaluation results

#### Scenario: Run evaluation from different space
- **WHEN** user tries to run evaluation case from space-1 with `X-Space-ID: space-2`
- **THEN** system returns 404 NOT FOUND

### Requirement: Batch Evaluation

The system SHALL run batch evaluations only for cases in the current space.

#### Scenario: Batch run in space
- **WHEN** user requests batch evaluation with `X-Space-ID: space-1`
- **THEN** system runs all evaluation cases in space-1
- **AND** returns aggregated results

### Requirement: Evaluation Summary

The system SHALL return evaluation summary only for the current space.

#### Scenario: Get summary for space
- **WHEN** user requests evaluation summary with `X-Space-ID: space-1`
- **THEN** system returns summary of all evaluation runs in space-1
- **AND** runs from other spaces are NOT included
