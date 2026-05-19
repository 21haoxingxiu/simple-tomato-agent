## 1. Backend - Workspace CRUD API (Missing: create/update/delete)

- [x] 1.1 `Workspace` model already exists in `agent/db/models.py`
- [x] 1.2 `workspace_id` columns already exist on all resource tables
- [x] 1.3 `GET /api/auth/workspaces` already exists for listing workspaces
- [x] 1.4 Add `POST /api/auth/workspaces` - create new workspace
- [x] 1.5 Add `PATCH /api/auth/workspaces/{id}` - update workspace name/description
- [x] 1.6 Add `DELETE /api/auth/workspaces/{id}` - soft delete workspace
- [x] 1.7 Add `GET /api/auth/workspaces/{id}` - get single workspace details

## 2. Backend - Workspace Isolation (Already implemented)

- [x] 2.1 `X-Workspace-ID` header filtering in knowledge router
- [x] 2.2 `X-Workspace-ID` header filtering in chat router
- [x] 2.3 `X-Workspace-ID` header filtering in eval router
- [x] 2.4 Add workspace validation middleware to ensure workspace exists and belongs to user

## 3. Backend - RAG Pipeline Workspace Support (Already implemented)

- [x] 3.1 `workspace_id` in vector metadata during ingestion
- [x] 3.2 Vector retrieval filters by workspace_id
- [x] 3.3 BM25 indexes by workspace

## 4. Gateway - Workspace Context (Already implemented)

- [x] 4.1 `X-Workspace-ID` header forwarded to Agent
- [x] 4.2 CORS allows `X-Workspace-ID` header

## 5. Frontend - Workspace State Management (Already implemented)

- [x] 5.1 `useWorkspaceStore` exists in `store/workspace.ts`
- [x] 5.2 `activeWorkspaceId` persisted to localStorage
- [x] 5.3 `getWorkspaceId()` in API client reads from store
- [x] 5.4 `X-Workspace-ID` header sent with all API requests

## 6. Frontend - Workspace Selector UI (Partially implemented)

- [x] 6.1 `WorkspaceSelector` component exists
- [x] 6.2 Workspace selector in Header
- [x] 6.3 Workspace dropdown with list/switch functionality
- [x] 6.4 Implement "新建工作区" button functionality
- [x] 6.5 Add workspace creation modal
- [ ] 6.6 Add workspace settings/edit functionality (optional enhancement)

## 7. Frontend - API Client Updates

- [x] 7.1 Add `workspaceApi.create()` function
- [x] 7.2 Add `workspaceApi.update()` function
- [x] 7.3 Add `workspaceApi.delete()` function

## 8. Testing

- [ ] 8.1 Test workspace CRUD operations
- [ ] 8.2 Test workspace isolation between users
- [ ] 8.3 Test workspace deletion cascade

## 9. Documentation

- [ ] 9.1 Update API documentation with workspace endpoints
