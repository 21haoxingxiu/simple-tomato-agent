## Context

AgentStudio is an enterprise AI agent platform with knowledge base, RAG, conversation, evaluation, and voice capabilities. Currently, all resources are shared globally without isolation. For multi-tenant or multi-team scenarios, we need workspace-level isolation so different groups can have their own data silos.

**Current State:**
- Knowledge bases, conversations, and evaluation cases are stored without space context
- No concept of workspace or tenant isolation
- All users can access all data (ACL is basic, not space-scoped)

**Stakeholders:**
- Enterprise users needing tenant isolation
- Team admins managing team workspaces
- Platform operators managing multi-tenant deployments

## Goals / Non-Goals

**Goals:**
- Introduce Space (Workspace) as the top-level isolation unit
- Scope all resources (knowledge bases, conversations, evaluations) to a space
- Provide space CRUD operations via API and UI
- Ensure data isolation between spaces at database and application layer
- Support space switching in the UI

**Non-Goals:**
- User-space permission model (RBAC) - out of scope for this change
- Space billing/quota management
- Cross-space data sharing
- Space templates or presets

## Decisions

### D1: Space Context Propagation via Header

**Decision:** Use `X-Space-ID` HTTP header to propagate space context across services.

**Rationale:**
- Keeps URL structure clean (no space ID in every path)
- Consistent with existing JWT-based auth pattern
- Easy to implement middleware in both Gateway (Go) and Agent (Python)
- Frontend can set header from state (Zustand store)

**Alternatives Considered:**
- Path-based (`/api/spaces/{id}/knowledge/...`): More RESTful but requires URL restructuring
- JWT claim: Requires token refresh on space switch, more complex

### D2: Space ID as Non-Nullable Foreign Key

**Decision:** Add `space_id` as non-nullable foreign key to all resource tables.

**Rationale:**
- Database-level referential integrity
- Simplifies queries (no null checks)
- Data migration creates a "default" space for existing data

**Migration Strategy:**
1. Create `spaces` table
2. Create default space with ID `default`
3. Add nullable `space_id` column to resource tables
4. Update all rows to have `space_id = 'default'`
5. Make `space_id` non-nullable with foreign key constraint

### D3: Vector Store Partitioning by Space

**Decision:** Include `space_id` in vector metadata for filtering.

**Rationale:**
- Chroma/Milvus support metadata filtering
- Avoids creating separate collections per space (collection overhead)
- Query filter: `{"space_id": "<current_space>"}`

**Trade-off:** Slightly higher query overhead due to filtering, but simpler management.

### D4: Space Selection Stored in Frontend State

**Decision:** Store selected space ID in Zustand store + localStorage, not in JWT.

**Rationale:**
- Avoids JWT refresh on space switch
- Persists across sessions via localStorage
- Backend validates space access on each request

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Data migration may be slow for large datasets | Run migration in batches; provide progress indicator |
| Forgotten `X-Space-ID` header causes cross-space data leak | Middleware validates header presence; API returns 400 if missing |
| Vector store queries slower with metadata filter | Index `space_id` metadata; monitor query performance |
| Frontend state desync (localStorage vs server) | Validate space exists on app load; reset to default if invalid |

## Migration Plan

### Phase 1: Database Schema
1. Create `spaces` table
2. Create default space
3. Add `space_id` columns (nullable) to resource tables
4. Populate `space_id` for existing records

### Phase 2: Backend Changes
1. Add space middleware in Gateway and Agent
2. Update API handlers to filter by space
3. Update RAG pipeline with space-aware vector queries
4. Add space management API endpoints

### Phase 3: Frontend Changes
1. Add space selector component
2. Update Zustand store for space state
3. Update API client to include `X-Space-ID` header
4. Update UI to show space context

### Rollback Strategy
- Reversible migration: Keep original columns, add `space_id` as nullable
- Feature flag: `ENABLE_MULTI_SPACE=true` to activate new behavior
- If issues arise, disable flag and system works without space isolation

## Open Questions

1. Should space deletion be soft-delete or hard-delete?
   - **Recommendation:** Soft-delete with 30-day retention for recovery

2. What happens to vector embeddings when a space is deleted?
   - **Recommendation:** Delete vectors with matching `space_id` metadata

3. Should there be a limit on number of spaces per user?
   - **Deferred:** Leave unbounded for now, add quota later if needed
