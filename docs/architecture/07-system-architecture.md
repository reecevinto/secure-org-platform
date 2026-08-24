# 7. System Architecture

## 7.0 Purpose

The Secure Organization Management Platform will be designed as a production-oriented, multi-tenant SaaS platform.

The architecture must support:

- Secure authentication
- Multi-factor authentication
- Multi-tenancy
- Granular RBAC
- Resource-level authorization
- Organization management
- Teams
- Projects
- Documents
- Notifications
- API keys
- Audit logging
- Billing
- Background jobs
- REST APIs
- Observability
- Automated testing
- CI/CD
- Cloud deployment
- Failure recovery
- Security assessment

The architecture must also directly address the threats identified in Step 6.

---

## 7.1 Architectural Goals

| Goal | Objective |
|---|---|
| Security | Protect identities, tenants, data, APIs and infrastructure |
| Tenant Isolation | Prevent cross-organization access |
| Maintainability | Keep responsibilities separated |
| Scalability | Allow components to scale independently where appropriate |
| Reliability | Minimize single points of failure |
| Testability | Make components independently testable |
| Observability | Make system behavior measurable |
| Deployability | Support reproducible deployments |
| Security Testing | Make security controls testable |
| Operability | Make the system practical to operate |

---

## 7.2 Architectural Principles

```
Security by Design
        ↓
Least Privilege
        ↓
Defense in Depth
        ↓
Explicit Trust Boundaries
        ↓
Server-Side Authorization
        ↓
Tenant Isolation
        ↓
Separation of Concerns
        ↓
Stateless Application Services Where Practical
        ↓
Observable Systems
        ↓
Automated Testing
        ↓
Infrastructure as Code
        ↓
Reproducible Deployments
```

---

## 7.3 Initial Architectural Style

We will not start with dozens of microservices — that would add complexity without necessarily adding engineering value.

The initial architecture will use a:

> **Modular Monolith with supporting infrastructure services**

This gives us:

- Clear domain boundaries
- Simpler local development
- Simpler deployment
- Easier debugging
- Strong transactional consistency
- Easier testing
- Lower operational overhead

while still allowing individual components to be extracted later if there is a genuine reason.

This is an important architectural decision. We are deliberately avoiding:

> *"Microservices because production systems use microservices."*

Instead:

> **Use the simplest architecture that can satisfy the requirements while preserving clear boundaries and future scalability.**

---

## 7.4 High-Level Architecture

The initial target architecture:

```
                         INTERNET
                             │
                             ▼
                    ┌─────────────────┐
                    │      DNS        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  CDN / Edge     │
                    │  Protection     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Reverse Proxy / │
                    │ Load Balancer   │
                    └────────┬────────┘
                             │
                       HTTPS / TLS
                             │
             ┌───────────────┴───────────────┐
             │                               │
             ▼                               ▼
      ┌─────────────┐                ┌─────────────┐
      │   Frontend  │                │  Public API │
      │     Web     │                │             │
      └──────┬──────┘                └──────┬──────┘
             │                              │
             └──────────────┬───────────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Application Backend │
                 │   Modular Monolith  │
                 └──────────┬──────────┘
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 │ PostgreSQL  │     │    Redis    │     │   Object    │
 │  Database   │     │    Cache    │     │   Storage   │
 └─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │ Job Queue   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Worker    │
                    │   Process   │
                    └──────┬──────┘
                           │
              ┌────────────┼─────────────┐
              ▼            ▼             ▼
           Email        Billing       Notifications
          Provider      Provider        Provider
```

This is our logical architecture at this stage. The precise cloud topology will be determined later.

---

## 7.5 Major System Components

- Frontend
- Backend API
- Background Worker
- PostgreSQL
- Redis
- Object Storage
- Message / Job Queue
- Reverse Proxy / Load Balancer
- Observability Stack
- CI/CD Pipeline
- Infrastructure

---

## 7.6 Frontend Architecture

The frontend will provide the user-facing application.

**Primary responsibilities:**

- Authentication UI
- Dashboard
- Organization Management
- User Management
- Team Management
- Project Management
- Document Management
- RBAC Management
- Notifications
- API Key Management
- Billing
- Audit Logs
- Settings
- Administrative Interfaces

The frontend must not be trusted for authorization. For example:

```
Frontend:  "Hide Delete User button."

                ≠

Security:  "User is authorized to delete this user."
```

The backend remains authoritative.

---

## 7.7 Backend Architecture

The backend will be the primary security and business-logic boundary.

```
Backend
│
├── API Layer
├── Authentication
├── Authorization
├── Organizations
├── Users
├── Memberships
├── Roles
├── Permissions
├── Teams
├── Projects
├── Documents
├── Notifications
├── API Keys
├── Audit
├── Billing
├── Administration
└── Background Jobs
```

---

## 7.8 Layered Backend Architecture

Inside the backend, we will maintain separation between:

```
                    API / HTTP
                        │
                        ▼
                   Controllers
                        │
                        ▼
                    Services
                        │
                        ▼
                 Domain Logic
                        │
                        ▼
                 Repositories
                        │
                        ▼
                    Database
```

Supporting concerns sit across these layers:

- Authentication
- Authorization
- Validation
- Logging
- Metrics
- Tracing
- Error Handling
- Security Controls

The purpose is to prevent controllers from becoming giant blocks of business logic.

---

## 7.9 Domain-Oriented Backend Structure

The backend should be organized around business domains rather than one enormous collection of technical folders.

```
backend/
└── src/
    │
    ├── auth/
    ├── users/
    ├── organizations/
    ├── memberships/
    ├── roles/
    ├── permissions/
    ├── teams/
    ├── projects/
    ├── documents/
    ├── notifications/
    ├── api-keys/
    ├── audit/
    ├── billing/
    ├── administration/
    │
    ├── common/
    ├── infrastructure/
    └── config/
```

The exact technology-specific structure will be finalized during Step 11 — Engineering Standards.

---

## 7.10 Authentication Boundary

**Authentication** establishes: *Who is this user?*

**Authorization** establishes: *What is this user allowed to do?*

These must remain conceptually separate.

```
Request
   ↓
Authentication
   ↓
Identity Established
   ↓
Authorization
   ↓
Permission Evaluation
   ↓
Business Operation
```

---

## 7.11 Authorization Architecture

Authorization is one of the most important architectural components. We need to evaluate:

```
Identity + Organization Membership + Role + Permission + Resource + Action
```

Conceptually:

```
User
 │
 ├── Organization Membership
 │
 ├── Role
 │
 └── Permissions
        │
        ▼
   Authorization
        │
        ▼
Resource + Action
```

**Example — Allowed:**

```
User → Member of Organization A → Project Manager
     → projects:update → Project 123 → Organization A → ALLOW
```

**Example — Denied:**

```
User → Member of Organization A → Project Manager
     → Project 999 → Organization B → DENY
```

This architecture directly addresses our Step 6 cross-tenant access threat.

---

## 7.12 Multi-Tenant Architecture

We will use a **shared application / shared database model** with strict tenant-aware data isolation for the initial system.

```
                   PostgreSQL
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Organization A   Organization B   Organization C
```

Each tenant-owned resource will be associated with an organization/tenant identifier:

```
organizations
     │
     ├── users/memberships
     ├── teams
     ├── projects
     ├── documents
     ├── notifications
     ├── API keys
     └── audit events
```

The exact database enforcement strategy will be finalized during Step 8 — Database Design.

---

## 7.13 Tenant Isolation Principle

Every tenant-owned request must carry an authorization context.

```
Authenticated User
        │
        ▼
Organization Context
        │
        ▼
Authorization Check
        │
        ▼
Resource Lookup
        │
        ▼
Tenant Validation
        │
        ▼
Operation
```

We will avoid relying on the frontend to supply a trusted tenant identifier. The backend must establish the authorized organization context.

---

## 7.14 Database Architecture

PostgreSQL will serve as the primary transactional datastore.

**Responsibilities:**

- Users
- Organizations
- Memberships
- Roles
- Permissions
- Teams
- Projects
- Documents metadata
- Notifications
- API Keys metadata
- Audit Records
- Billing metadata

The database design itself comes in Step 8. At this stage we are establishing the architectural responsibility.

---

## 7.15 Redis Architecture

Redis may support:

- Caching
- Rate limiting
- Short-lived state
- Job queue infrastructure
- Session-related ephemeral data where appropriate

> **Important:** Redis will not automatically become the source of truth for business-critical data. PostgreSQL remains the authoritative transactional datastore.

---

## 7.16 Object Storage Architecture

Documents and potentially other large objects should not be stored directly inside PostgreSQL as normal application records.

```
Application
    │
    ▼
Authorization
    │
    ▼
Object Storage
```

PostgreSQL stores metadata such as:

```
document_id
organization_id
owner
storage_reference
filename
content_type
size
created_at
```

The actual object resides in object storage.

---

## 7.17 Background Processing

Some operations should not block an HTTP request, for example:

- Send email
- Generate reports
- Process notifications
- Process billing events
- Document processing
- Audit processing where appropriate
- Scheduled tasks
- Cleanup operations

**Architecture:**

```
API
 │
 ▼
Job Queue
 │
 ▼
Worker
 │
 ├── Email
 ├── Notifications
 ├── Billing
 ├── Processing
 └── Scheduled Tasks
```

---

## 7.18 API Architecture

The platform will expose versioned REST APIs, conceptually under `/api/v1/`:

```
/api/v1/auth
/api/v1/users
/api/v1/organizations
/api/v1/teams
/api/v1/projects
/api/v1/documents
/api/v1/notifications
/api/v1/api-keys
/api/v1/audit
/api/v1/billing
```

The exact API contract will be designed in Step 9 — API Design.

---

## 7.19 API Request Pipeline

Every protected request should conceptually flow through:

```
HTTP Request
     ↓
TLS / Edge
     ↓
Rate Limiting
     ↓
Request Validation
     ↓
Authentication
     ↓
Authorization
     ↓
Tenant Context
     ↓
Business Logic
     ↓
Database / Service
     ↓
Audit Event
     ↓
Response
```

Not every endpoint will require exactly the same controls, but this represents our security-oriented baseline.

---

## 7.20 Audit Architecture

Security-sensitive actions should generate audit events, for example:

- Login
- Logout
- MFA changes
- Password changes
- Role changes
- Permission changes
- User creation
- User deletion
- API key creation
- API key revocation
- Document access
- Administrative actions
- Billing changes

```
Business Operation
       │
       ├──────────────► Audit Event
       │
       ▼
   Response
```

Audit logging should not expose secrets or sensitive credentials.

---

## 7.21 Observability Architecture

Observability will eventually include:

**Logs**
- Application logs
- Security logs
- Audit logs
- Infrastructure logs

**Metrics**
- Request latency
- Error rate
- Request rate
- Database performance
- Queue depth
- Worker failures
- Authentication failures
- Rate-limit events

**Traces**

```
Request → API → Service → Database → External provider
```

The observability architecture will be implemented later.

---

## 7.22 Security Architecture

The architecture incorporates multiple security layers:

```
                    INTERNET
                       │
                       ▼
                TLS / Edge Security
                       │
                       ▼
                 Rate Limiting
                       │
                       ▼
                 Authentication
                       │
                       ▼
                 Authorization
                       │
                       ▼
                 Tenant Isolation
                       │
                       ▼
                Input Validation
                       │
                       ▼
                Business Logic
                       │
                       ▼
                Database Controls
                       │
                       ▼
                  Audit Logs
                       │
                       ▼
                  Monitoring
```

This implements the defense-in-depth principle from Step 6.

---

## 7.23 Secret Management Architecture

Secrets should not be committed to Git. The architecture will distinguish:

```
Source Code  ≠  Configuration  ≠  Secrets
```

| Environment | Approach |
|---|---|
| Development | Local secret configuration |
| Production | Managed secret store |
| CI/CD | Short-lived / scoped credentials where possible |

The specific implementation will be determined during cloud and infrastructure design.

---

## 7.24 External Integrations

The system may eventually integrate with:

- Email Provider
- Payment Provider
- Object Storage
- Monitoring
- Identity-related services

External integrations must be treated as separate trust boundaries.

```
Application
     │
     ▼
Integration Adapter
     │
     ▼
External Provider
```

This prevents external-provider-specific logic from contaminating the core business domains.

---

## 7.25 Failure Boundaries

We must explicitly design for failures, including:

- Database unavailable
- Redis unavailable
- Queue unavailable
- Email provider unavailable
- Billing provider unavailable
- Object storage unavailable
- Worker crashes
- Application instance crashes
- Network timeout
- Third-party API timeout

The architecture should distinguish **critical** vs. **non-critical** dependencies. For example:

```
Database unavailable      → Application may become unavailable
Email provider unavailable → User operation may still succeed
                            → Email job can retry
```

This becomes particularly important during Steps 19–20 (Observability and Failure Testing).

---

## 7.26 Deployment Architecture

The eventual deployment will look conceptually like:

```
                     CLOUD
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
        Load Balancer       Object Storage
              │
              ▼
       ┌───────────────┐
       │ Application   │
       │ Containers    │
       └───────┬───────┘
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
   Database   Redis    Queue
       │                │
       │                ▼
       │             Workers
       │
       ▼
    Backups
```

The actual cloud provider and service selection should be determined later rather than prematurely locking us into a specific platform.

---

## 7.27 Environment Architecture

```
Development → Staging → Production
```

Each environment should have:

- Separate configuration
- Separate secrets
- Separate databases/resources where appropriate
- Separate access controls

Production must never depend on a developer's local environment.

---

## 7.28 CI/CD Architecture

The future pipeline:

```
Developer
   ↓
Git Push
   ↓
CI
   ├── Lint
   ├── Type Checks
   ├── Unit Tests
   ├── Integration Tests
   ├── Security Scans
   ├── Dependency Scans
   └── Build
          ↓
      Container
          ↓
      Artifact
          ↓
       Staging
          ↓
   Validation
          ↓
     Production
```

This connects architecture to the later DevSecOps phase.

---

## 7.29 Infrastructure as Code

Infrastructure will eventually be represented as code:

```
infrastructure/
│
├── networking/
├── compute/
├── database/
├── storage/
├── monitoring/
├── security/
└── environments/
```

The exact structure will be defined later.

---

## 7.30 Network Architecture

The eventual production network should separate public-facing components from private infrastructure.

```
                  INTERNET
                     │
                     ▼
              Public Edge
                     │
                     ▼
              Load Balancer
                     │
              ───────┴───────
                     │
              Private Network
                     │
             ┌───────┼───────┐
             ▼       ▼       ▼
        Application Worker Services
             │       │       │
             └───────┼───────┘
                     │
             ┌───────┼────────┐
             ▼       ▼        ▼
          Database  Redis   Storage
```

Databases and internal services should not be unnecessarily exposed directly to the public Internet.

---

## 7.31 Architecture and Threat Traceability

The architecture must directly respond to Step 6.

| Threat | Architectural Response |
|---|---|
| Account Takeover | Dedicated authentication boundary |
| Broken Access Control | Central authorization architecture |
| Cross-Tenant Access | Tenant-aware domain/data model |
| Privilege Escalation | Explicit RBAC/authorization |
| IDOR/BOLA | Resource-level authorization |
| Session Compromise | Dedicated session architecture |
| Injection | Validation + safe persistence layer |
| XSS | Secure frontend/backend boundaries |
| CSRF | Authentication-aware request protection |
| File Upload | Isolated object-storage architecture |
| API Abuse | Edge/rate-limit layer |
| API Key Compromise | Dedicated credential-management domain |
| Secret Exposure | Externalized secret management |
| Audit Tampering | Dedicated audit subsystem |
| DoS | Rate limits + resource controls |
| Supply Chain | CI/CD security controls |
| CI/CD Compromise | Protected pipeline architecture |
| Cloud Misconfiguration | IaC + private infrastructure |

---

## 7.32 Architectural Decisions

We begin an **Architecture Decision Record (ADR)** practice.

### ADR-001 — Modular Monolith

**Decision:** Use a modular monolith as the initial application architecture.

**Reasoning:**
- Reduces unnecessary operational complexity
- Allows strong domain boundaries
- Simplifies local development
- Simplifies transactions
- Simplifies testing
- Allows future service extraction
- Appropriate for the initial scale

**Rejected alternative:** Microservices from day one.

**Reason:** Premature distributed-system complexity would increase operational and debugging overhead without a demonstrated requirement.

---

### ADR-002 — Shared Database Multi-Tenancy

**Decision:** Use a shared PostgreSQL deployment with tenant-aware data isolation initially.

**Reasoning:**
- Efficient resource usage
- Simpler operations
- Easier local development
- Appropriate for the initial platform
- Can evolve toward stronger isolation models if requirements demand it

**Security requirement:** Tenant isolation must be enforced server-side and tested explicitly.

---

### ADR-003 — PostgreSQL as Primary Database

**Decision:** Use PostgreSQL as the primary transactional datastore.

**Reasoning:**
- Relational integrity
- Transactions
- Mature ecosystem
- Strong indexing/query capabilities
- Suitable for complex authorization relationships
- Suitable for multi-tenant SaaS data

---

### ADR-004 — Object Storage for Documents

**Decision:** Store document objects in object storage while storing metadata in PostgreSQL.

**Reasoning:**
- Appropriate for large objects
- Scalable
- Separates metadata from binary content
- Easier backup/storage management

---

### ADR-005 — Asynchronous Background Jobs

**Decision:** Use background workers for operations that do not need to block the primary request.

**Reasoning:**
- Improves request latency
- Enables retries
- Isolates failures
- Supports scheduled processing

---

## 7.33 Architecture Quality Attributes

Our architecture will be evaluated against:

- Security
- Reliability
- Availability
- Scalability
- Performance
- Maintainability
- Testability
- Observability
- Deployability
- Recoverability

We will not simply say the architecture is "production-grade." We will eventually demonstrate these qualities through:

- Tests
- Metrics
- Security assessments
- Load tests
- Failure experiments
- Deployment automation
- Documentation

---

## 7.34 Step 7 Deliverables

| Deliverable | Status |
|---|---|
| Architectural goals | ✅ |
| Architectural principles | ✅ |
| Architectural style | ✅ |
| High-level architecture | ✅ |
| Component architecture | ✅ |
| Backend architecture | ✅ |
| Frontend boundary | ✅ |
| Authentication architecture | ✅ |
| Authorization architecture | ✅ |
| Multi-tenant architecture | ✅ |
| Database responsibility | ✅ |
| Cache responsibility | ✅ |
| Object storage architecture | ✅ |
| Background processing architecture | ✅ |
| API architecture | ✅ |
| Audit architecture | ✅ |
| Observability architecture | ✅ |
| Security architecture | ✅ |
| Secret management strategy | ✅ |
| External integration boundaries | ✅ |
| Failure boundaries | ✅ |
| Deployment architecture | ✅ |
| Environment architecture | ✅ |
| CI/CD architecture | ✅ |
| IaC direction | ✅ |
| Network architecture | ✅ |
| Threat-to-architecture traceability | ✅ |
| Initial ADRs | ✅ |

**Step 7 is now established.**
