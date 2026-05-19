## Why

The current platform lacks workspace isolation - all users share the same knowledge bases, conversations, and evaluation data. For enterprise scenarios with multiple teams or tenants, data isolation is essential. Each space should have its own isolated conversations, knowledge bases, and evaluation cases.

## What Changes

- Add **Space (Workspace)** concept as the top-level isolation unit
- All existing resources (knowledge bases, conversations, evaluation cases) will belong to a specific space
- Users can switch between spaces they have access to
- Data is completely isolated between spaces

### New Capabilities

- `space-management`: CRUD operations for spaces, including creation, listing, updating, and deletion of workspaces
- `space-isolation`: Resource isolation layer ensuring conversations, knowledge bases, and evaluations are scoped to specific spaces

### Modified Capabilities

- `knowledge-base`: Knowledge base CRUD and document management will be scoped to a space
- `conversation`: Chat sessions and history will be isolated per space
- `evaluation`: Evaluation cases and runs will be scoped to a space

## Impact

### Backend (Agent - Python/FastAPI)
- Database schema changes: Add `spaces` table, add `space_id` foreign key to existing tables
- API changes: All resource endpoints require `space_id` context (via header or path parameter)
- RAG pipeline: Vector store and BM25 indices need space-aware partitioning

### Backend (Gateway - Go/Gin)
- JWT token may need to include current space context
- Routing changes: Space context propagation to Agent service

### Frontend (Next.js)
- Add space selector in header/sidebar
- Update all API calls to include space context
- Space-specific routing structure

### Database
- Migration: Create `spaces` table
- Migration: Add `space_id` column to `knowledge_bases`, `conversations`, `eval_cases` tables
- Data migration: Create default space and assign existing data
