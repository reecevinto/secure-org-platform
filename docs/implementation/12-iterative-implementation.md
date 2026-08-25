# 12. Iterative Implementation

We are finally going to start building the actual Secure Organization Management Platform — and we're going to do it exactly according to the workflow we've established, not by generating thousands of lines of disconnected code.

---

## 12.0 Where We Are Now

```
01. Problem Definition                    ✅
02. Requirements                          ✅
03. Users / Actors / Roles                ✅
04. Functional Requirements               ✅
05. Non-Functional Requirements           ✅
06. Threat Model                          ✅
07. System Architecture                   ✅
08. Database Design                       ✅
09. API Design                            ✅
10. Repository                            ✅
11. Engineering Standards                 ✅
─────────────────────────────────────────────
12. IMPLEMENTATION                         🚀 NOW
─────────────────────────────────────────────
13. Testing                               ⏭
14. Security Testing                      ⏭
15. Containerization                      ⏭
16. CI/CD                                 ⏭
17. Infrastructure as Code                ⏭
18. Cloud Deployment                      ⏭
19. Observability                         ⏭
20. Failure Testing                       ⏭
21. Security Assessment                   ⏭
22. Documentation                         ⏭
23. Portfolio Case Study                  ⏭
24. Public Release                        ⏭
```

Steps 1–11 are not separate school assignments. They are the blueprint for what we are about to build.

---

## 12.1 How We Will Implement

We will use an incremental/iterative engineering workflow. Every meaningful feature will follow:

```
Requirement
     ↓
Design
     ↓
Implementation
     ↓
Unit Tests
     ↓
Integration Tests
     ↓
Security Validation
     ↓
Code Review
     ↓
Git Commit
     ↓
Next Feature
```

So instead of *"build the entire SaaS application,"* we will do:

```
Foundation
    ↓
Configuration
    ↓
Application bootstrap
    ↓
Database foundation
    ↓
Authentication foundation
    ↓
User management
    ↓
Organizations
    ↓
Memberships
    ↓
RBAC
    ↓
Projects
    ↓
Documents
    ↓
Notifications
    ↓
API keys
    ↓
Audit logging
    ↓
Billing
    ↓
Analytics
    ↓
Frontend
    ↓
Integration
```

Each stage will be tested before moving forward.

---

## 12.2 First Rule: Don't Code Yet

Even though we're at implementation, we should not immediately start writing business logic. First we're going to establish the actual application foundation.

The first implementation phase will be **12A — Project Foundation**, establishing:

1. Technology stack
2. Runtime versions
3. Monorepo/application structure
4. Backend foundation
5. Frontend foundation
6. Database connection foundation
7. Environment configuration
8. Dependency management
9. Development tooling
10. Testing framework
11. Code quality tooling
12. Local development workflow

Only after that do we begin implementing actual domain functionality.

---

## 12.3 Technology Stack

We should deliberately choose a modern, employable stack rather than choosing technologies randomly. For this flagship project:

### Frontend
- Next.js
- TypeScript
- React
- Tailwind CSS

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database
- PostgreSQL

### Authentication

We will build the authentication architecture ourselves rather than blindly dropping in an authentication package and hiding the security decisions. We will use established cryptographic/security libraries where appropriate.

### Background Jobs

Initially: **Redis + Celery**, or an equivalent architecture depending on the final implementation requirements. We will not introduce unnecessary distributed complexity simply to look impressive.

### Testing

- Backend: `pytest`
- Frontend: `Vitest`, `Playwright`

### API Documentation

OpenAPI — FastAPI will help generate the API specification, but we will still deliberately design and review the contract.

### Containerization
- Docker
- Docker Compose

### CI/CD
- GitHub Actions

### Infrastructure
- Terraform

### Cloud

We'll select the cloud platform deliberately when we reach the infrastructure phase.

### Observability

We'll eventually introduce OpenTelemetry, Prometheus, Grafana, and centralized logging. The exact production architecture will be decided based on requirements and cost rather than adding every tool immediately.

---

## 12.4 Target Application Architecture

**Initial local architecture:**

```
                 ┌─────────────────────┐
                 │      Browser        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      Next.js        │
                 │     Frontend        │
                 └──────────┬──────────┘
                            │ HTTPS
                            ▼
                 ┌─────────────────────┐
                 │      FastAPI        │
                 │      Backend        │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌─────────────┐
        │PostgreSQL│  │  Redis   │  │ Background  │
        │          │  │          │  │   Workers   │
        └──────────┘  └──────────┘  └─────────────┘
```

**Later — cloud architecture:**

```
                    Cloud
                      │
              ┌───────┴────────┐
              │ Load Balancer  │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │ Application     │
              │ Containers      │
              └───────┬────────┘
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
 PostgreSQL         Redis        Object Storage
       │
       ▼
 Backups
```

**Eventually — observability:**

```
Application
     │
     ├── Logs ────────► Logging
     ├── Metrics ─────► Metrics
     └── Traces ──────► Tracing
```

---

## 12.5 Repository Evolution

Our repository will now begin becoming an actual software project. Eventually:

```
secure-org-platform/
│
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
│
├── frontend/
│
├── backend/
│
├── tests/
│
├── infrastructure/
│
├── docker/
│
├── scripts/
│
├── docs/
│
└── .github/
    └── workflows/
```

But again: we introduce these incrementally. We don't create 50 empty folders just for appearance.

---

## 12.6 Implementation Milestone Structure

Step 12 is divided into major milestones.

### Milestone 12.1 — Development Foundation
- Repository foundation
- Runtime configuration
- Environment management
- Backend bootstrap
- Frontend bootstrap
- Database connectivity
- Testing foundation
- Linting
- Formatting
- Type checking

### Milestone 12.2 — Identity Foundation
- User model
- Password hashing
- Registration
- Login
- Sessions
- Logout
- Password security

### Milestone 12.3 — Authentication Security
- MFA
- Session rotation
- Session expiration
- Account recovery
- Brute-force protection
- Security events

### Milestone 12.4 — Organizations
- Organization creation
- Organization settings
- Memberships
- Invitations
- Membership lifecycle

### Milestone 12.5 — Authorization / RBAC

> **This will be one of the most important security milestones.**

- Roles
- Permissions
- Role assignment
- Permission evaluation
- Resource authorization
- Tenant isolation

### Milestone 12.6 — Core Business Domains
- Teams
- Projects
- Documents

### Milestone 12.7 — Platform Services
- Notifications
- Background jobs
- API keys
- Audit logs
- Analytics

### Milestone 12.8 — Billing
- Plans
- Subscriptions
- Usage
- Billing state
- Payment integration
- Webhook handling

### Milestone 12.9 — Frontend Application
- Authentication UI
- Dashboard
- Organization management
- User management
- RBAC interface
- Projects
- Documents
- Notifications
- Settings
- Administration
- Analytics
- Billing

### Milestone 12.10 — Full Integration

```
Frontend
    ↓
API
    ↓
Services
    ↓
Database
    ↓
Background jobs
    ↓
External integrations
```

---

## 12.7 Security Will Be Built Into Each Milestone

We're not going to wait until Step 14 to think about security.

**Authentication** — password attacks, credential stuffing, session theft, session fixation, MFA bypass, account enumeration

**Organizations** — unauthorized membership, invitation abuse, organization enumeration, cross-tenant access

**RBAC** — privilege escalation, horizontal privilege escalation, vertical privilege escalation, permission bypass

**Documents** — unauthorized access, IDOR/BOLA, path traversal, malicious uploads, cross-tenant data access

**API Keys** — secret leakage, improper scope, unauthorized reuse, rotation failure, revocation failure

This connects directly back to our Step 6 threat model.

---

## 12.8 Our First Implementation Slice

We will not begin with authentication. The first coding slice should establish the foundation upon which authentication and everything else will depend.

So our first actual implementation target will be **12.1 — Development Foundation**, specifically:

1. Confirm technology versions
2. Establish backend project
3. Establish frontend project
4. Establish environment configuration
5. Establish PostgreSQL development database
6. Establish database connectivity
7. Establish migration system
8. Establish testing foundation
9. Establish formatting/linting
10. Establish initial application health endpoint

The first endpoint will be something intentionally simple such as:

```
GET /health
```

But even that tiny endpoint will establish: application startup, configuration loading, routing, response validation, testing, logging foundation.

Then we'll commit it.

---

## 12.9 Git Workflow From This Point Forward

This is where our Git workflow becomes even more important. Instead of one massive Step 12 commit, we'll have commits such as:

```
chore: establish backend project foundation

chore: establish frontend application foundation

chore: configure development environment

feat: establish database connectivity

feat: add database migration framework

feat: add application health endpoint

test: establish backend testing foundation

chore: configure linting formatting and type checking
```

This will make your GitHub history tell a real engineering story.

---

## 12.10 What We Will NOT Do

- ❌ Generate the entire backend at once.
- ❌ Generate the entire frontend at once.
- ❌ Copy a random GitHub SaaS template.
- ❌ Add technologies just to make the architecture look complicated.
- ❌ Skip tests.
- ❌ Treat frontend authorization as security.
- ❌ Hard-code secrets.
- ❌ Commit `.env` files.
- ❌ Build features without connecting them to requirements.
- ❌ Build features without considering the threat model.
- ❌ Move forward with broken tests.
- ❌ Hide technical decisions.

---

## 12.11 The Bigger Career Objective

This project is not merely *"a SaaS application."* It is going to demonstrate the intersection of:

```
Full-Stack Engineering
        +
Application Security
        +
Cloud Engineering
        +
DevOps
        +
DevSecOps
        +
SRE
        +
Security Testing
```

That combination is the positioning we're building toward.

The GitHub repository should eventually allow a technical recruiter or engineering manager to see:

```
Problem
  ↓
Requirements
  ↓
Threat Model
  ↓
Architecture
  ↓
Database
  ↓
API
  ↓
Engineering Standards
  ↓
Real Code
  ↓
Tests
  ↓
Security Testing
  ↓
Docker
  ↓
CI/CD
  ↓
Terraform
  ↓
Cloud
  ↓
Observability
  ↓
Failure Testing
  ↓
Security Assessment
  ↓
Case Study
```

That is substantially stronger than having ten small tutorial repositories.

---

## 12.12 What We Do Next

Do not start writing application code yet. Our immediate next step is:

> **Step 12.1 — Development Foundation**

We'll first make the final technology/tooling decisions, verify what's installed on the local machine, establish the repository structure, and then create the first implementation slice.

From this point onward, the workflow is hands-on:

```
Exact step given
        ↓
Step executed
        ↓
Output reviewed
        ↓
Result verified
        ↓
Fixes applied as necessary
        ↓
Commit
        ↓
Push
        ↓
Next implementation slice
```
