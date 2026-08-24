# 8. Database Design

## 8.0 Purpose

The database will provide the authoritative transactional data layer for the Secure Organization Management Platform.

It must support:

- Organizations
- Users
- Memberships
- Roles
- Permissions
- Teams
- Projects
- Documents
- Notifications
- API Keys
- Audit Logs
- Billing
- Sessions
- MFA
- Background Job Metadata

The database must also enforce and support: tenant isolation, referential integrity, authorization relationships, data consistency, transactional operations, uniqueness constraints, secure credential handling, auditing, scalability, backup and recovery, and efficient querying.

Our primary database will be **PostgreSQL** — established in Step 7.

---

## 8.1 Database Design Goals

| Goal | Requirement |
|---|---|
| Integrity | Data must remain internally consistent |
| Security | Sensitive data must be protected |
| Tenant Isolation | Tenant-owned data must not cross boundaries |
| Performance | Common queries must be efficiently indexed |
| Scalability | Schema must support growth |
| Maintainability | Schema must be understandable and evolvable |
| Auditability | Security-sensitive operations must be traceable |
| Reliability | Transactions must protect critical operations |
| Recoverability | Data must be backup/recovery friendly |
| Testability | Database behavior must be testable |

---

## 8.2 Database Architectural Model

```
                    PostgreSQL
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
    Identity        Authorization     Business
     Domain            Domain          Domain
        │               │                │
        ▼               ▼                ▼
     Users           Roles          Organizations
     Sessions        Permissions    Teams
     MFA             Memberships    Projects
                                     Documents
                                     Notifications
                                     Billing
```

The database is shared at the infrastructure level, but tenant-owned records are logically isolated through organization relationships and authorization enforcement.

---

## 8.3 Core Domain Model

At the highest level:

```
User
 │
 ├── Membership
 │       │
 │       └── Organization
 │               │
 │               ├── Teams
 │               ├── Projects
 │               ├── Documents
 │               ├── Notifications
 │               ├── API Keys
 │               └── Audit Events
 │
 └── Authentication Data
```

This relationship is foundational.

---

## 8.4 Core Entities

The initial database will contain the following major entities.

| Domain | Entities |
|---|---|
| Identity | `users`, `user_sessions`, `mfa_credentials` |
| Organizations | `organizations`, `organization_memberships` |
| Authorization | `roles`, `permissions`, `role_permissions` |
| Teams | `teams`, `team_memberships` |
| Projects | `projects`, `project_memberships` |
| Documents | `documents`, `document_versions` |
| Notifications | `notifications`, `notification_preferences` |
| API | `api_keys` |
| Auditing | `audit_logs` |
| Billing | `subscriptions`, `billing_events` |

This is our initial logical model.

---

## 8.5 Entity Relationship Overview

**Core identity and organization chain:**

```
                         USERS
                           │
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
             USER SESSIONS       MFA
                    │
                    │
                    ▼
             ORGANIZATION
             MEMBERSHIPS
                    │
                    ▼
              ORGANIZATIONS
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
     TEAMS       PROJECTS     DOCUMENTS
       │            │            │
       │            │            ▼
       │            │      DOCUMENT VERSIONS
       │            │
       │            ▼
       │      PROJECT MEMBERS
       │
       ▼
 TEAM MEMBERS
```

**Authorization chain:**

```
ORGANIZATION MEMBERSHIP
          │
          ▼
         ROLE
          │
          ▼
    ROLE PERMISSIONS
          │
          ▼
     PERMISSIONS
```

**Auditing chain:**

```
USER
 │
 ▼
AUDIT LOG
 │
 ├── Organization
 ├── Resource
 ├── Action
 └── Result
```

---

## 8.6 `users`

The `users` table represents a platform identity.

```
users
--------------------------------
id
email
password_hash
first_name
last_name
status
email_verified_at
last_login_at
created_at
updated_at
deleted_at
```

**Important design decision:** We do not store a `plaintext_password`. Passwords are represented only by secure password hashes. The exact hashing algorithm will be determined during implementation/security engineering, but the architecture must support a modern password-hashing function.

---

## 8.7 User Identity

A user is a platform-level identity. One user may belong to multiple organizations:

```
Alice
 │
 ├── Organization A → Administrator
 │
 ├── Organization B → Member
 │
 └── Organization C → Project Manager
```

Therefore: **roles must not be stored directly on the global user record.** Instead:

```
User → Organization Membership → Role
```

This is critical for multi-tenancy.

---

## 8.8 `organizations`

Represents a tenant/customer organization.

```
organizations
--------------------------------
id
name
slug
status
created_at
updated_at
deleted_at
```

Each organization becomes a tenant boundary — Organization A, Organization B, Organization C must remain logically isolated.

---

## 8.9 `organization_memberships`

This is one of the most important tables in the entire system.

```
organization_memberships
--------------------------------
id
organization_id
user_id
role_id
status
joined_at
created_at
updated_at
```

**Relationships:**

```
organization_memberships.organization_id → organizations.id
organization_memberships.user_id         → users.id
organization_memberships.role_id         → roles.id
```

This table establishes **who belongs to which organization and what role they have there.**

---

## 8.10 Why Membership Is Separate

Consider Alice, who belongs to:

```
Company A → Owner
Company B → Member
Company C → Auditor
```

If `role_id` lived directly on `users`, we could not represent this correctly. Therefore:

```
users
  │
  ▼
organization_memberships
  │
  ├── organization_id
  ├── user_id
  └── role_id
```

This is the correct architectural model.

---

## 8.11 Roles

The `roles` table represents authorization roles.

```
roles
--------------------------------
id
organization_id
name
description
is_system_role
created_at
updated_at
```

We distinguish between:

**System roles** — Platform Administrator, Organization Owner, Organization Administrator, Member, Auditor

**Custom organization roles** — e.g., Project Manager, Security Analyst, Document Manager, Finance Manager

The exact role model will be finalized against the authorization requirements.

---

## 8.12 Permissions

Permissions represent individual capabilities, for example:

```
users:read       users:create      users:update      users:delete
projects:read    projects:create   projects:update   projects:delete
documents:read   documents:create  documents:update  documents:delete
audit:read       billing:read      billing:manage
```

```
permissions
--------------------------------
id
name
description
resource
action
created_at
```

---

## 8.13 Role-Permission Relationship

A role can have many permissions; a permission can belong to many roles.

```
roles
   │
   │  many-to-many
   ▼
role_permissions
   ▲
   │
permissions
```

```
role_permissions
--------------------------------
role_id
permission_id
created_at
```

This is a classic many-to-many relationship.

---

## 8.14 Authorization Model

Our authorization database model becomes:

```
USER → ORGANIZATION MEMBERSHIP → ROLE → ROLE PERMISSIONS → PERMISSION → RESOURCE
```

**Example — Allowed:**

```
Alice → Organization A → Project Manager → projects:update
      → Project 123 → Organization A → ALLOW
```

**Example — Denied:**

```
Alice → Organization A → Project 999 → Organization B → DENY
```

This is how the database design connects directly to our threat model.

---

## 8.15 Teams

Teams belong to organizations.

```
teams
--------------------------------
id
organization_id
name
description
created_by
created_at
updated_at
```

```
Organization
     │
     └── Teams
```

---

## 8.16 Team Memberships

Users may belong to multiple teams.

```
team_memberships
--------------------------------
team_id
user_id
joined_at
created_at
```

```
User
 │
 ├── Team A
 ├── Team B
 └── Team C
```

The organization boundary must still be respected — a user cannot be assigned to a team belonging to an organization they do not legitimately belong to.

---

## 8.17 Projects

Projects belong to organizations.

```
projects
--------------------------------
id
organization_id
name
description
status
created_by
created_at
updated_at
deleted_at
```

```
Organization
     │
     └── Projects
```

---

## 8.18 Project Memberships

Projects may have explicit membership.

```
project_memberships
--------------------------------
project_id
user_id
role
joined_at
created_at
```

This allows more granular authorization. For example:

```
Organization Role: Member
Project Role:      Project Manager
```

This lets us distinguish organization-level authority from resource-level authority.

---

## 8.19 Documents

Documents belong to an organization and potentially a project.

```
documents
--------------------------------
id
organization_id
project_id
owner_id
storage_key
filename
content_type
size_bytes
status
created_at
updated_at
deleted_at
```

The actual file content will be stored in object storage. PostgreSQL stores the metadata.

---

## 8.20 Document Versions

Documents may need versioning.

```
document_versions
--------------------------------
id
document_id
version_number
storage_key
size_bytes
checksum
created_by
created_at
```

```
Document
   │
   ├── Version 1
   ├── Version 2
   ├── Version 3
   └── Version N
```

This supports version history, integrity verification, recovery, and auditability.

---

## 8.21 Notifications

Notifications belong to users.

```
notifications
--------------------------------
id
user_id
organization_id
type
title
message
status
read_at
created_at
```

Organization context should be preserved where relevant.

---

## 8.22 Notification Preferences

Users should control notification preferences.

```
notification_preferences
--------------------------------
id
user_id
organization_id
notification_type
email_enabled
in_app_enabled
created_at
updated_at
```

---

## 8.23 API Keys

API keys are sensitive credentials. We must not store raw API keys in plaintext if the system can operate without doing so.

```
api_keys
--------------------------------
id
organization_id
created_by
name
key_prefix
key_hash
scopes
expires_at
last_used_at
revoked_at
created_at
```

The system can display the full secret once during creation while storing only the necessary verification representation. This will be revisited during security implementation.

---

## 8.24 Sessions

Authentication sessions should be represented separately from users.

```
user_sessions
--------------------------------
id
user_id
session_identifier
created_at
expires_at
last_seen_at
revoked_at
ip_address
user_agent
```

Sensitive session values should be handled carefully. The exact session architecture will be finalized during authentication implementation.

---

## 8.25 MFA

MFA credentials should not be mixed into the general user record.

```
mfa_credentials
--------------------------------
id
user_id
type
secret_reference
enabled_at
last_used_at
created_at
updated_at
```

Potential future types: TOTP, WebAuthn, Recovery Codes. Sensitive secrets must be protected appropriately.

---

## 8.26 Audit Logs

Audit logging is critical to the platform.

```
audit_logs
--------------------------------
id
organization_id
actor_user_id
action
resource_type
resource_id
result
ip_address
user_agent
metadata
created_at
```

**Example:**

```
actor_user_id = Alice
action        = "role.updated"
resource_type = "organization_member"
resource_id   = 123
result        = "success"
```

---

## 8.27 Audit Design Principles

Audit records should be:

- Append-oriented
- Difficult to modify
- Timestamped
- Attributable to an actor where possible
- Tenant-aware
- Free from plaintext secrets

**Never put into audit metadata:** password, API secret, MFA secret, session token, or any private credential.

---

## 8.28 Billing

Billing data will be separated from core authorization data.

```
subscriptions
--------------------------------
id
organization_id
provider
provider_customer_id
provider_subscription_id
plan
status
current_period_start
current_period_end
created_at
updated_at
```

```
billing_events
--------------------------------
id
organization_id
provider_event_id
event_type
payload_reference
status
processed_at
created_at
```

External billing-provider identifiers should have appropriate uniqueness constraints.

---

## 8.29 Tenant Ownership Matrix

Every major entity should have a clearly defined ownership model.

| Entity | Tenant Owned? | Ownership |
|---|---|---|
| User | No | Global identity |
| Session | No | User |
| MFA | No | User |
| Organization | Root | Organization |
| Membership | Yes | Organization |
| Role | Usually | Organization |
| Permission | Usually global | Platform |
| Team | Yes | Organization |
| Project | Yes | Organization |
| Project Membership | Yes | Project/Organization |
| Document | Yes | Organization |
| Document Version | Yes | Document |
| Notification | Yes | User/Organization |
| API Key | Yes | Organization |
| Audit Log | Yes | Organization |
| Subscription | Yes | Organization |
| Billing Event | Yes | Organization |

This table will become extremely useful during security testing.

---

## 8.30 Foreign Keys

We will use foreign keys extensively. For example:

```
organization_memberships.organization_id → organizations.id
organization_memberships.user_id         → users.id
```

This prevents orphaned relationships.

---

## 8.31 Unique Constraints

| Constraint | Rule |
|---|---|
| `users.email` | Must be unique according to the identity model |
| `organizations.slug` | Should be unique |
| `(user_id, organization_id)` on membership | Should be unique — a user should not have duplicate memberships in the same organization |
| `(role_id, permission_id)` | Should be unique |
| `(team_id, user_id)` | Should be unique |
| `(project_id, user_id)` | Should be unique |

---

## 8.32 Indexing Strategy

Indexes will be designed around actual access patterns. Likely indexes include:

```
users(email)
organizations(slug)
organization_memberships(user_id)
organization_memberships(organization_id)
teams(organization_id)
projects(organization_id)
documents(organization_id)
documents(project_id)
audit_logs(organization_id, created_at)
notifications(user_id, status)
api_keys(organization_id)
subscriptions(organization_id)
```

We will not blindly index every column. Indexes have costs:

```
More indexes → Faster reads + Slower writes + More storage
```

Indexing must be evidence-driven.

---

## 8.33 Soft Deletion

Some entities may require soft deletion, conceptually via `deleted_at`. This may apply to: Users, Organizations, Projects, Documents.

We should not blindly use soft deletion everywhere — it creates complexity around uniqueness, queries, restoration, privacy, cascading relationships, and storage growth. This decision will be made per entity.

---

## 8.34 Transaction Boundaries

Critical operations must use database transactions. Example:

```
Create Organization
        │
        ├── Create Organization
        ├── Create Owner Membership
        ├── Assign Owner Role
        └── Create Initial Configuration
```

These should succeed together or fail together:

```
BEGIN
   ↓
Create Organization
   ↓
Create Membership
   ↓
Assign Role
   ↓
COMMIT
```

If something fails: `ROLLBACK`.

---

## 8.35 Concurrency

The database design must account for concurrent operations, such as:

- Two administrators editing the same resource
- Two users accepting an invitation
- Two workers processing the same billing event
- Two requests attempting to consume the same API key

We will use appropriate transactions, unique constraints, locking, idempotency, and isolation levels where necessary.

---

## 8.36 Idempotency

Certain operations must be safely repeatable — especially billing webhooks, background jobs, external provider callbacks, and critical mutations.

**Example:**

```
Provider Event: evt_123

If received twice:
  First  → Process
  Second → Detect existing event → Do not duplicate
```

This is why `provider_event_id` should have an appropriate uniqueness constraint.

---

## 8.37 Data Classification

| Classification | Examples |
|---|---|
| **Public** | Organization display name, public project information |
| **Internal** | Operational metadata, internal configuration |
| **Confidential** | User information, audit records, billing information |
| **Highly Sensitive** | Password hashes, MFA secrets, session credentials, API key verification material, security credentials |

This classification will influence encryption, logging, access controls, and retention.

---

## 8.38 Encryption

We need encryption at multiple layers:

```
Application → TLS → Database connection → Database encryption at rest
```

Sensitive application-level secrets may additionally require application-level encryption or secure secret storage.

We explicitly distinguish **encryption at rest** from **encryption of sensitive application data** — they are not the same thing.

---

## 8.39 Data Retention

Different data types may require different retention policies — audit logs, billing events, sessions, notifications, deleted records, documents.

Retention policies must be documented rather than deleting data arbitrarily. This will eventually connect to privacy, compliance, disaster recovery, and storage management.

---

## 8.40 Database Migrations

The database schema will be version controlled through migrations:

```
migrations/
│
├── 001_initial_schema
├── 002_add_mfa
├── 003_add_api_keys
├── 004_add_audit_indexes
└── ...
```

A production database must never depend on manually remembering which SQL commands were executed.

---

## 8.41 Database Security

```
Least-privilege database users
        ↓
Private network access
        ↓
TLS connections
        ↓
Credential management
        ↓
Backups
        ↓
Audit/monitoring
        ↓
Restricted administrative access
```

The application should not connect using an unrestricted database superuser.

---

## 8.42 Database Access Architecture

The application should conceptually interact with PostgreSQL through controlled data-access layers:

```
HTTP Request
     ↓
Controller
     ↓
Service
     ↓
Authorization
     ↓
Repository / Data Access
     ↓
PostgreSQL
```

We do not want arbitrary SQL scattered throughout controllers.

---

## 8.43 Tenant-Aware Querying

Tenant-owned queries must explicitly account for organization context.

**Correct:**

```sql
SELECT project
WHERE project.id = requested_id
AND project.organization_id = authorized_organization_id
```

**Incorrect:**

```sql
SELECT project
WHERE project.id = requested_id
```

The second pattern can create IDOR/BOLA vulnerabilities. This is one of the most important security properties of the database architecture.

---

## 8.44 Defense in Depth for Tenant Isolation

Tenant isolation should not depend on one mechanism. We want:

```
Application Authorization
        +
Tenant-Aware Queries
        +
Foreign Key Integrity
        +
Database Constraints
        +
Automated Security Tests
        +
Security Assessment
```

Depending on the final PostgreSQL architecture, we may also evaluate database-level controls such as Row-Level Security. That decision should be made based on the actual application architecture rather than adding it merely for appearance.

---

## 8.45 Initial Logical Schema

```
users
│
├── user_sessions
├── mfa_credentials
│
└── organization_memberships
        │
        ├── organizations
        │       │
        │       ├── teams
        │       │      └── team_memberships
        │       │
        │       ├── projects
        │       │      └── project_memberships
        │       │
        │       ├── documents
        │       │      └── document_versions
        │       │
        │       ├── notifications
        │       │      └── notification_preferences
        │       │
        │       ├── api_keys
        │       │
        │       ├── audit_logs
        │       │
        │       └── subscriptions
        │              └── billing_events
        │
        └── roles
                │
                └── role_permissions
                        │
                        └── permissions
```

---

## 8.46 Preliminary Relationship Map

```
User
 │
 ├──< Sessions
 ├──< MFA Credentials
 └──< Organization Memberships
             │
             ├──> Organization
             │
             └──> Role
                     │
                     └──< Role Permissions >── Permission


Organization
 │
 ├──< Teams
 │      └──< Team Memberships >── User
 │
 ├──< Projects
 │      └──< Project Memberships >── User
 │
 ├──< Documents
 │      └──< Document Versions
 │
 ├──< Notifications
 │
 ├──< API Keys
 │
 ├──< Audit Logs
 │
 └──< Subscription
          └──< Billing Events
```

---

## 8.47 Database-to-Threat Traceability

Our Step 6 threats now have concrete database responses.

| Threat | Database Response |
|---|---|
| Cross-Tenant Access | `organization_id` ownership model |
| IDOR/BOLA | Tenant-aware resource queries |
| Privilege Escalation | Membership → Role → Permission model |
| Account Takeover | Separate sessions/MFA data |
| API Key Theft | Hash/verification representation |
| Audit Tampering | Append-oriented audit model |
| Duplicate Billing | Unique provider event IDs |
| Orphaned Data | Foreign keys |
| Unauthorized Relationships | Constraints + authorization |
| Data Leakage | Classification + access controls |
| Credential Exposure | No plaintext secrets |
| Data Corruption | Transactions + constraints |

---

## 8.48 What We Are Deliberately NOT Doing Yet

We are not starting to write:

- `CREATE TABLE ...`
- SQL migrations
- Physical column types (e.g. `VARCHAR(255)`)
- Code/ORM models

**Why?** Because Step 8 is database *design*, not database *implementation*. We first need the logical model. Then we will make the physical schema concrete.

---

## 8.49 Step 8 Deliverables

| Deliverable | Status |
|---|---|
| Database goals | ✅ |
| Database architecture | ✅ |
| PostgreSQL decision | ✅ |
| Entity inventory | ✅ |
| Entity relationships | ✅ |
| Identity model | ✅ |
| Organization model | ✅ |
| Membership model | ✅ |
| RBAC data model | ✅ |
| Team model | ✅ |
| Project model | ✅ |
| Document model | ✅ |
| Notification model | ✅ |
| API key model | ✅ |
| Session model | ✅ |
| MFA model | ✅ |
| Audit model | ✅ |
| Billing model | ✅ |
| Tenant ownership matrix | ✅ |
| Foreign-key strategy | ✅ |
| Unique constraints | ✅ |
| Indexing strategy | ✅ |
| Soft-delete strategy | ✅ |
| Transaction strategy | ✅ |
| Concurrency strategy | ✅ |
| Idempotency strategy | ✅ |
| Data classification | ✅ |
| Encryption strategy | ✅ |
| Retention strategy | ✅ |
| Migration strategy | ✅ |
| Database security | ✅ |
| Tenant-aware querying | ✅ |
| Threat traceability | ✅ |

**Step 8 is now established.**
