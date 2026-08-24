# 9. API Design

## 9.0 Purpose

The API layer will provide the controlled interface between the frontend, external clients, background services, and the platform's business logic.

The API design must be derived from the full engineering lifecycle so far:

```
Step 2 — Requirements
        ↓
Step 3 — Users / Roles
        ↓
Step 4 — Functional Requirements
        ↓
Step 5 — Non-Functional Requirements
        ↓
Step 6 — Threat Model
        ↓
Step 7 — Architecture
        ↓
Step 8 — Database Design
        ↓
Step 9 — API Design
```

The objective is to define a versioned, secure, predictable, documented REST API before implementation begins.

---

## 9.1 API Design Goals

The API must provide:

- Clear resource-oriented endpoints
- Consistent request/response formats
- Authentication
- Authorization
- Tenant isolation
- Input validation
- Error handling
- Rate limiting
- Pagination
- Filtering
- Sorting
- Idempotency where required
- Auditability
- API versioning
- Secure API key support
- Appropriate HTTP semantics
- Consistent status codes
- Observability
- Backward compatibility

---

## 9.2 API Style

The initial API architecture will use:

```
REST + JSON + HTTPS + Versioned endpoints
```

**Base URL concept:** `https://api.example.com/v1`

**Local development:** `http://localhost:<port>/api/v1`

The production domain will be determined later.

---

## 9.3 API Versioning

The initial version will be `/v1`, for example:

```
/api/v1/auth/login
/api/v1/organizations
/api/v1/projects
```

Future breaking changes may introduce `/v2`. We will avoid unnecessary version fragmentation.

---

## 9.4 Authentication Model

The API will support authenticated requests through the authentication architecture defined earlier.

```
Client
  ↓
HTTPS
  ↓
Authentication
  ↓
Session / Credential Validation
  ↓
Authorization
  ↓
Tenant Context
  ↓
Business Logic
  ↓
Database
```

**Authentication** answers: *Who are you?*

**Authorization** answers: *Are you allowed to perform this action?*

These must remain separate concerns.

---

## 9.5 Authentication Endpoints

**Initial authentication API surface:**

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/verify-email
POST   /api/v1/auth/resend-verification
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

**MFA:**

```
POST   /api/v1/auth/mfa/setup
POST   /api/v1/auth/mfa/verify
POST   /api/v1/auth/mfa/disable
GET    /api/v1/auth/mfa/status
```

The exact authentication mechanism will be finalized during implementation.

---

## 9.6 Authentication Security Requirements

Authentication endpoints must have stronger protections than ordinary endpoints. Requirements include:

- HTTPS
- Rate limiting
- Credential protection
- Input validation
- Generic authentication errors
- Brute-force protection
- Session management
- MFA enforcement
- Audit logging
- Suspicious-event monitoring

For example, login failures should not reveal whether an email address exists. Avoid responses such as *"User does not exist"* when that would enable account enumeration.

---

## 9.7 Current User

```
GET /api/v1/auth/me
```

Returns the authenticated user's current identity and relevant context.

```json
{
  "id": "user-id",
  "email": "user@example.com",
  "first_name": "Example",
  "last_name": "User",
  "email_verified": true
}
```

The actual response schema will be formalized in the API contract.

---

## 9.8 Organization APIs

Organizations are first-class resources.

```
GET    /api/v1/organizations
POST   /api/v1/organizations
GET    /api/v1/organizations/{organization_id}
PATCH  /api/v1/organizations/{organization_id}
DELETE /api/v1/organizations/{organization_id}
```

**Membership:**

```
GET    /api/v1/organizations/{organization_id}/members
POST   /api/v1/organizations/{organization_id}/members/invitations
GET    /api/v1/organizations/{organization_id}/members/{member_id}
PATCH  /api/v1/organizations/{organization_id}/members/{member_id}
DELETE /api/v1/organizations/{organization_id}/members/{member_id}
```

---

## 9.9 Organization Authorization

A user must not be able to access an organization merely because they know its ID. For example, `GET /api/v1/organizations/org-123` must result in:

```
Authenticate user
       ↓
Determine organization membership
       ↓
Determine role
       ↓
Determine permission
       ↓
Authorize request
       ↓
Return resource
```

Otherwise: `403 Forbidden`, or, where appropriate, a deliberately non-disclosing response.

---

## 9.10 Organization Context

For organization-owned resources, the API must establish tenant context.

```
Organization A → Project 123
```

A user belonging only to Organization B must not be able to retrieve Project 123 simply by changing `/project/123` to another known ID. This directly addresses the IDOR/BOLA threat from Step 6.

---

## 9.11 User APIs

**Administrative user management:**

```
GET    /api/v1/organizations/{organization_id}/users
GET    /api/v1/organizations/{organization_id}/users/{user_id}
PATCH  /api/v1/organizations/{organization_id}/users/{user_id}
DELETE /api/v1/organizations/{organization_id}/users/{user_id}
```

The system must distinguish:

```
Current authenticated user  ≠  Organization administrator  ≠  Platform administrator
```

---

## 9.12 Role APIs

**Organization role management:**

```
GET    /api/v1/organizations/{organization_id}/roles
POST   /api/v1/organizations/{organization_id}/roles
GET    /api/v1/organizations/{organization_id}/roles/{role_id}
PATCH  /api/v1/organizations/{organization_id}/roles/{role_id}
DELETE /api/v1/organizations/{organization_id}/roles/{role_id}
```

**Role permissions:**

```
GET  /api/v1/organizations/{organization_id}/roles/{role_id}/permissions
PUT  /api/v1/organizations/{organization_id}/roles/{role_id}/permissions
```

---

## 9.13 Permission Model

Permissions follow `resource:action`, for example:

```
users:read       users:create      users:update      users:delete
projects:read    projects:create   projects:update   projects:delete
documents:read    documents:create documents:update  documents:delete
audit:read        billing:read     billing:manage
```

The API should never trust a permission supplied by the frontend. This is unsafe:

```json
{ "role": "admin" }
```

...and assuming the client is telling the truth. The server determines authorization from trusted server-side state.

---

## 9.14 Teams API

```
GET    /api/v1/organizations/{organization_id}/teams
POST   /api/v1/organizations/{organization_id}/teams

GET    /api/v1/organizations/{organization_id}/teams/{team_id}
PATCH  /api/v1/organizations/{organization_id}/teams/{team_id}
DELETE /api/v1/organizations/{organization_id}/teams/{team_id}
```

**Team membership:**

```
GET    /api/v1/organizations/{organization_id}/teams/{team_id}/members
POST   /api/v1/organizations/{organization_id}/teams/{team_id}/members
DELETE /api/v1/organizations/{organization_id}/teams/{team_id}/members/{user_id}
```

---

## 9.15 Projects API

```
GET    /api/v1/organizations/{organization_id}/projects
POST   /api/v1/organizations/{organization_id}/projects

GET    /api/v1/organizations/{organization_id}/projects/{project_id}
PATCH  /api/v1/organizations/{organization_id}/projects/{project_id}
DELETE /api/v1/organizations/{organization_id}/projects/{project_id}
```

**Project members:**

```
GET    /api/v1/organizations/{organization_id}/projects/{project_id}/members
POST   /api/v1/organizations/{organization_id}/projects/{project_id}/members
PATCH  /api/v1/organizations/{organization_id}/projects/{project_id}/members/{user_id}
DELETE /api/v1/organizations/{organization_id}/projects/{project_id}/members/{user_id}
```

---

## 9.16 Documents API

```
GET    /api/v1/organizations/{organization_id}/documents
POST   /api/v1/organizations/{organization_id}/documents

GET    /api/v1/organizations/{organization_id}/documents/{document_id}
PATCH  /api/v1/organizations/{organization_id}/documents/{document_id}
DELETE /api/v1/organizations/{organization_id}/documents/{document_id}
```

**Versions:**

```
GET /api/v1/organizations/{organization_id}/documents/{document_id}/versions
GET /api/v1/organizations/{organization_id}/documents/{document_id}/versions/{version_id}
```

File upload/download architecture will be designed around object storage rather than unnecessarily routing large files through the application server.

---

## 9.17 Notifications API

```
GET   /api/v1/notifications
PATCH /api/v1/notifications/{notification_id}
POST  /api/v1/notifications/{notification_id}/read
POST  /api/v1/notifications/read-all
```

**Preferences:**

```
GET   /api/v1/notification-preferences
PATCH /api/v1/notification-preferences
```

---

## 9.18 API Key Management

**Organization API keys:**

```
GET    /api/v1/organizations/{organization_id}/api-keys
POST   /api/v1/organizations/{organization_id}/api-keys
GET    /api/v1/organizations/{organization_id}/api-keys/{key_id}
DELETE /api/v1/organizations/{organization_id}/api-keys/{key_id}
POST   /api/v1/organizations/{organization_id}/api-keys/{key_id}/rotate
```

**Security rules:**

```
Never return the secret after initial creation
        ↓
Store verification material securely
        ↓
Support expiration
        ↓
Support revocation
        ↓
Support scopes
        ↓
Audit usage
```

---

## 9.19 Audit API

Audit logs should be **read-only** through the API.

```
GET /api/v1/organizations/{organization_id}/audit-logs
GET /api/v1/organizations/{organization_id}/audit-logs/{audit_id}
```

**Filtering:** actor, action, resource, resource_id, result, date range.

Audit records should not be editable through normal application APIs.

---

## 9.20 Billing API

```
GET   /api/v1/organizations/{organization_id}/subscription
POST  /api/v1/organizations/{organization_id}/subscription
PATCH /api/v1/organizations/{organization_id}/subscription
POST  /api/v1/organizations/{organization_id}/subscription/cancel
```

Provider webhooks should use a separate endpoint:

```
POST /api/v1/webhooks/billing
```

Webhook processing must include:

```
Signature validation
        ↓
Event identification
        ↓
Idempotency
        ↓
Authorization of webhook source
        ↓
Processing
        ↓
Audit/logging
```

---

## 9.21 HTTP Methods

We will use HTTP semantics consistently.

| Method | Purpose |
|---|---|
| GET | Retrieve resource |
| POST | Create/trigger operation |
| PUT | Replace resource |
| PATCH | Partially update resource |
| DELETE | Delete/deactivate resource |

We should not use `POST /delete-user` when `DELETE /users/{id}` properly represents the operation.

---

## 9.22 HTTP Status Codes

We will standardize responses.

**Success**

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted |
| 204 | No Content |

**Client errors**

| Code | Meaning |
|---|---|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Content |
| 429 | Too Many Requests |

**Server errors**

| Code | Meaning |
|---|---|
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

The exact usage of each code will be documented.

---

## 9.23 Standard Error Response

Errors should have a predictable structure.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "request_id": "req_123"
  }
}
```

For field-level validation:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed.",
    "fields": {
      "email": [
        "Must be a valid email address."
      ]
    },
    "request_id": "req_123"
  }
}
```

We must avoid leaking: SQL errors, stack traces, internal paths, database details, secrets, or implementation details to clients.

---

## 9.24 Request IDs

Every API request should have a correlation/request identifier.

```
Client
  ↓
X-Request-ID
  ↓
API
  ↓
Application Logs
  ↓
Database/Audit Events
  ↓
Observability Platform
```

This will become extremely valuable during Step 19 — Observability.

---

## 9.25 Pagination

Collection endpoints should support pagination.

```
GET /api/v1/organizations/org-123/projects?page=2&page_size=25
```

We should establish a maximum page size (`page_size <= configured maximum`). Clients must not be allowed to request millions of records in one response. For high-volume resources, we can evaluate cursor-based pagination.

---

## 9.26 Filtering

Resources may support controlled filtering:

```
GET /projects?status=active
GET /audit-logs?action=user.login
```

Filters must be explicitly supported. We should not allow arbitrary database fields to become query parameters without validation.

---

## 9.27 Sorting

Controlled sorting:

```
GET /projects?sort=created_at
GET /projects?sort=-created_at
```

The server should whitelist sortable fields. Never translate arbitrary client input directly into SQL.

---

## 9.28 Rate Limiting

Different API categories will have different limits:

```
Authentication              → Strict rate limits
Password reset               → Very strict limits
Normal authenticated APIs    → Standard limits
Internal trusted operations  → Different policy
```

The actual numbers will be established during implementation and performance testing. Responses should communicate throttling appropriately, including `429 Too Many Requests`.

---

## 9.29 Idempotency

Certain mutation endpoints should support idempotency — especially billing, payments, external side effects, important resource creation, and webhook processing.

```
Idempotency-Key: abc123
```

```
Repeated request → same key → same operation → do not duplicate side effect
```

---

## 9.30 API Key Authentication

Machine clients may use API keys:

```
Authorization: Bearer <credential>
```

The server must determine:

```
Which key?
        ↓
Which organization?
        ↓
Which scopes?
        ↓
Is it expired?
        ↓
Is it revoked?
        ↓
Is requested operation permitted?
```

An API key must not automatically grant unrestricted organization access.

---

## 9.31 Authorization Pipeline

Every protected request conceptually passes through:

```
HTTP Request
     ↓
TLS termination
     ↓
Request ID
     ↓
Rate Limiting
     ↓
Authentication
     ↓
Tenant Resolution
     ↓
Authorization
     ↓
Input Validation
     ↓
Business Logic
     ↓
Database
     ↓
Audit Event
     ↓
Response
```

This is a critical part of the API architecture.

---

## 9.32 Input Validation

Every external input must be validated. Sources include: path parameters, query parameters, headers, JSON bodies, multipart forms, webhook payloads.

Validation must occur server-side. Never assume *"the frontend already validated it."*

---

## 9.33 Output Validation

Responses should also follow defined schemas. Benefits: predictable clients, reduced accidental data leakage, easier testing, easier documentation, safer API evolution.

For example, an internal user object might contain `password_hash`, security flags, internal identifiers — but the public API response must not expose those fields.

---

## 9.34 API Security Headers

The API infrastructure will eventually enforce appropriate HTTP security headers, for example:

```
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
```

The exact header policy depends on whether the response is API-only, browser-facing, or served through the frontend.

---

## 9.35 CORS

CORS must be explicitly configured. Avoid:

```
Access-Control-Allow-Origin: *
```

for authenticated browser APIs unless there is a deliberate reason. The production configuration should explicitly identify trusted frontend origins.

---

## 9.36 CSRF

CSRF protection depends on the authentication mechanism. If browser authentication uses cookies, we must consider: CSRF protection, SameSite cookie policy, secure cookies, origin/referer validation where appropriate.

If a different authentication architecture is used, the CSRF model changes. This decision will be finalized during implementation.

---

## 9.37 API Auditability

Security-sensitive API operations should produce audit events, for example:

```
login.success              login.failure
password.changed
mfa.enabled                mfa.disabled

organization.created       organization.updated

member.invited              member.removed

role.created                role.updated
role.assigned

api_key.created              api_key.revoked
api_key.rotated

document.created            document.deleted

billing.updated
```

This connects Step 9 directly to the audit database model from Step 8.

---

## 9.38 API Documentation

The API will eventually be documented using an OpenAPI specification.

```
docs/
└── api/
    ├── 09-api-design.md
    └── openapi.yaml
```

The OpenAPI specification should become a source of truth for: endpoints, parameters, request bodies, responses, authentication, error formats, schemas. We should eventually validate the implementation against the specification.

---

## 9.39 API Testing Strategy

Every endpoint category should eventually have:

- Happy-path tests
- Validation tests
- Authentication tests
- Authorization tests
- Tenant-isolation tests
- Error tests
- Rate-limit tests
- Abuse-case tests

**Example — GET Project:**

```
GET Project
   ↓
Authenticated?
   ↓
Organization member?
   ↓
Permission?
   ↓
Project belongs to organization?
   ↓
Project membership requirement?
   ↓
ALLOW / DENY
```

---

## 9.40 API Threat Traceability

| Threat | API Control |
|---|---|
| Broken Authentication | Authentication middleware |
| BOLA / IDOR | Tenant + resource authorization |
| Privilege Escalation | Server-side permission checks |
| Credential Stuffing | Rate limiting + authentication controls |
| Account Enumeration | Generic responses |
| API Key Abuse | Scoped keys + expiration + revocation |
| Injection | Input validation + parameterized queries |
| Excessive Data Exposure | Explicit response schemas |
| Mass Assignment | Explicit writable fields |
| DoS | Rate limits + pagination |
| Replay | Idempotency where required |
| Webhook Forgery | Signature validation |
| Information Leakage | Safe error responses |

---

## 9.41 Mass Assignment Protection

The API must never blindly bind every JSON field to a database model. Unsafe conceptual pattern:

```json
{
  "name": "Project",
  "organization_id": "attacker-controlled-id",
  "owner_id": "attacker-controlled-id",
  "is_admin": true
}
```

The server must explicitly determine which fields are writable:

| Source | Fields |
|---|---|
| Client-controlled | `name`, `description` |
| Server-controlled | `organization_id`, `owner_id`, `created_at`, `permissions` |

This is particularly important for our multi-tenant architecture.

---

## 9.42 API Resource Ownership

For every endpoint, we need to answer:

1. Who owns this resource?
2. Who can read it?
3. Who can create it?
4. Who can update it?
5. Who can delete it?
6. Who can administer it?

This should map directly to Step 3's roles and Step 4's functional requirements.

---

## 9.43 API Contract Example

A project creation request might conceptually be:

```http
POST /api/v1/organizations/{organization_id}/projects
Content-Type: application/json
Authorization: Bearer <credential>
```

**Request:**

```json
{
  "name": "Security Platform",
  "description": "Internal security project"
}
```

The server determines:

```
organization_id
        ↓
authenticated membership
        ↓
permission
        ↓
authorized creation
        ↓
server-generated project ID
        ↓
database transaction
        ↓
audit event
        ↓
201 Created
```

The client does not decide: `created_by`, `organization_id`, `permissions`, or the audit actor.

---

## 9.44 API Design Principles

```
Resource-oriented design
        ↓
Consistent semantics
        ↓
Explicit authorization
        ↓
Least privilege
        ↓
Secure defaults
        ↓
Validated input
        ↓
Controlled output
        ↓
Predictable errors
        ↓
Observability
        ↓
Backward compatibility
```

---

## 9.45 Step 9 Deliverables

| Deliverable | Status |
|---|---|
| API architecture | ✅ |
| REST conventions | ✅ |
| API versioning | ✅ |
| Authentication model | ✅ |
| Authentication endpoints | ✅ |
| Organization endpoints | ✅ |
| User endpoints | ✅ |
| Role endpoints | ✅ |
| Permission model | ✅ |
| Team endpoints | ✅ |
| Project endpoints | ✅ |
| Document endpoints | ✅ |
| Notification endpoints | ✅ |
| API key endpoints | ✅ |
| Audit endpoints | ✅ |
| Billing endpoints | ✅ |
| Webhook endpoints | ✅ |
| HTTP methods | ✅ |
| HTTP status codes | ✅ |
| Error schema | ✅ |
| Pagination | ✅ |
| Filtering | ✅ |
| Sorting | ✅ |
| Rate limiting | ✅ |
| Idempotency | ✅ |
| API key security | ✅ |
| Authorization pipeline | ✅ |
| Input validation | ✅ |
| Output validation | ✅ |
| CORS | ✅ |
| CSRF considerations | ✅ |
| Security headers | ✅ |
| Auditability | ✅ |
| OpenAPI strategy | ✅ |
| API testing strategy | ✅ |
| Threat traceability | ✅ |
| Mass-assignment protection | ✅ |

**Step 9 is now established.**
