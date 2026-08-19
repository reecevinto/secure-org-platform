# 3. Users, Actors & Roles

Step 3 establishes **who interacts with the system**, what they are responsible for, what they can access, and what trust level they hold.

This becomes the foundation for the RBAC model, authorization architecture, API authorization, database relationships, threat model, and security testing.

**Progress:**

| Step | Status |
|---|---|
| 1 — Problem Definition | ✅ |
| 2 — Requirements | ✅ |
| 3 — Users | ← We are here |

We are still not coding.

---

## 3.1 Purpose of Step 3

The platform is multi-tenant. We therefore need to answer:

> **Who can interact with the platform, and exactly what can each actor do?**

This document defines: user/actor categories, personas, platform actors, organization roles, responsibilities, permissions, access boundaries, trust levels, authentication requirements, the authorization model, role hierarchy, user lifecycle, organization lifecycle, administrative boundaries, external/system actors, permission principles, user workflows, and acceptance criteria.

---

## 3.2 Actor Model

We distinguish between human users and non-human actors.

```
                    PLATFORM
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      HUMAN          SYSTEM         EXTERNAL
      ACTORS         ACTORS          ACTORS
        │              │              │
        ▼              ▼              ▼
   Platform Admin   Background      API Client
   Org Owner        Worker          Email Service
   Org Admin        Scheduler       Object Storage
   Manager          Monitoring      Payment Provider*
   Standard User
   Read-Only User
```

\* Payment integration is a future capability.

---

## 3.3 Human Users

Six primary human roles are initially defined:

1. Platform Administrator
2. Organization Owner
3. Organization Administrator
4. Manager
5. Standard User
6. Read-Only User

These are roles, but they also represent the initial user personas.

---

## 3.4 Persona — Platform Administrator

**Identity:** A trusted operator responsible for the SaaS platform itself. This is not the same as an organization administrator — the Platform Administrator operates at the platform level.

**Responsibilities:**
- Platform configuration
- Platform health
- User support
- Security operations
- System administration
- Operational investigation
- Platform-level incident response

**Access scope:**

```
PLATFORM
   │
   ├── Organizations
   ├── Platform users
   ├── System configuration
   ├── Platform audit events
   └── Operational telemetry
```

**Important security boundary:** A Platform Administrator should not automatically receive unrestricted access to organization business data simply because they are a platform administrator. Administrative power should follow least privilege. Where privileged support access is required, it should be:

- Explicit
- Auditable
- Limited
- Time-bound where practical

---

## 3.5 Persona — Organization Owner

The Organization Owner represents the highest-level administrative authority inside a particular organization.

```
ACME Corporation
      │
      └── Organization Owner
              │
              ├── Organization Admins
              ├── Managers
              └── Users
```

**Responsibilities:**
- Organization settings
- User management
- Role management
- Team management
- Project management
- Subscription management
- API management
- Security configuration

**Scope:** Only their own organization.

```
Organization A          Organization B

Owner of A → ACCESS: A
            → NO ACCESS: B (unless separately authorized)
```

---

## 3.6 Persona — Organization Administrator

The Organization Administrator manages the day-to-day administration of an organization.

**Responsibilities:**
- User invitations
- User management
- Team management
- Role assignment
- Project administration
- Organization configuration
- Audit review

**Typical restrictions:** An Organization Administrator may not necessarily control:
- Billing ownership
- Organization deletion
- Ownership transfer
- High-risk security settings

Those may be restricted to the Organization Owner. This distinction gives us meaningful RBAC rather than simply having `admin = everything`.

---

## 3.7 Persona — Manager

A Manager operates within an organization but has a narrower administrative scope.

**Typical responsibilities:**
- Team management
- Project management
- Team membership
- Project membership
- Task/resource administration
- Team-level visibility

```
Organization
     │
     ├── Engineering
     │      └── Manager
     │
     ├── Marketing
     │      └── Manager
     │
     └── Finance
            └── Manager
```

The Engineering Manager should not automatically gain access to Finance resources.

---

## 3.8 Persona — Standard User

The Standard User represents the normal employee/member.

**Can:**
- Access assigned organizations
- Access permitted teams
- Access permitted projects
- View permitted documents
- Create/update permitted resources
- Receive notifications
- Manage their own profile
- Manage their own security settings

**Cannot automatically:**
- Manage organization users
- Assign privileged roles
- Modify organization-wide settings
- Access other organizations
- Access unauthorized projects

---

## 3.9 Persona — Read-Only User

The Read-Only User has intentionally restricted permissions.

**Typical use cases:** Auditor, external reviewer, stakeholder, executive viewer, temporary observer.

**May:**
- View permitted organizations/resources
- View permitted projects
- View permitted documents
- View permitted reports

**Generally cannot:**
- Modify resources
- Delete resources
- Manage users
- Change permissions
- Change organizational settings

---

## 3.10 Non-Human Actor — API Client

The API Client represents an external application integrating with the platform.

```
Company ERP
      │
      ▼
Secure Org Platform API
      │
      ▼
Organization Resources
```

API clients should not authenticate like normal browser users. They will use API credentials, which must be:

- Scoped
- Revocable
- Rotatable
- Auditable
- Rate-limited

This becomes particularly important when designing the API security model.

---

## 3.11 System Actor — Background Worker

The Background Worker performs asynchronous tasks:

- Send email
- Process notifications
- Generate reports
- Process documents
- Perform scheduled jobs
- Process audit-related tasks

The worker should not automatically have unrestricted database access. Again: **least privilege** — the worker gets only the permissions required for its specific responsibilities.

---

## 3.12 System Actor — Scheduler

The Scheduler initiates scheduled tasks:

- Cleanup expired sessions
- Process scheduled notifications
- Generate periodic reports
- Perform maintenance tasks
- Process retention policies

---

## 3.13 External Service Actors

Future integrations may include:

- Email provider
- Object storage
- Payment provider
- Identity provider
- Monitoring platform
- Logging/SIEM platform

These integrations will be explicitly scoped.

---

## 3.14 Role Hierarchy

At the organization level, the initial conceptual hierarchy is:

```
                 ORGANIZATION OWNER
                         │
                         ▼
              ORGANIZATION ADMIN
                         │
                         ▼
                     MANAGER
                         │
                         ▼
                   STANDARD USER
                         │
                         ▼
                  READ-ONLY USER
```

Hierarchy does not automatically mean inheritance of every permission — permissions are defined explicitly. This is important for security.

---

## 3.15 Role vs. Permission

**Role** — A collection of permissions. Example: `Manager`

**Permission** — A specific action. Example: `project:create`, `project:update`, `project:view`

```
Manager
    │
    ├── project:view
    ├── project:create
    ├── project:update
    └── team:view
```

This will eventually become database entities.

---

## 3.16 Initial Permission Model

Permissions are organized by resource.

**Organization**
- `organization:view`
- `organization:update`
- `organization:delete`
- `organization:manage_settings`

**Users**
- `user:view`
- `user:invite`
- `user:update`
- `user:deactivate`
- `user:remove`

**Roles**
- `role:view`
- `role:create`
- `role:update`
- `role:assign`
- `role:delete`

**Teams**
- `team:view`
- `team:create`
- `team:update`
- `team:delete`
- `team:manage_members`

**Projects**
- `project:view`
- `project:create`
- `project:update`
- `project:delete`
- `project:manage_members`

**Documents**
- `document:view`
- `document:create`
- `document:update`
- `document:delete`
- `document:download`

**Audit**
- `audit:view`

**API**
- `api_key:view`
- `api_key:create`
- `api_key:rotate`
- `api_key:revoke`

**Billing**
- `billing:view`
- `billing:manage`

This is the initial permission vocabulary, not yet the final authorization implementation.

---

## 3.17 Initial Role/Permission Matrix

| Capability | Platform Admin | Org Owner | Org Admin | Manager | User | Read-Only |
|---|---|---|---|---|---|---|
| Platform administration | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View organization | Support-level | ✅ | ✅ | ✅ | Assigned | Assigned |
| Modify organization | Controlled | ✅ | Limited | ❌ | ❌ | ❌ |
| Manage users | Platform-level | ✅ | ✅ | Limited | ❌ | ❌ |
| Assign roles | Platform-level | ✅ | ✅ | Limited | ❌ | ❌ |
| Manage teams | Platform-level | ✅ | ✅ | ✅ | Limited | ❌ |
| Manage projects | Platform-level | ✅ | ✅ | ✅ | Assigned | ❌ |
| View documents | Controlled | ✅ | ✅ | Assigned | Assigned | Assigned |
| Modify documents | Controlled | ✅ | ✅ | Assigned | Assigned | ❌ |
| View audit logs | Platform | ✅ | ✅ | Limited | ❌ | Limited |
| Manage API keys | Platform | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage billing | Platform | ✅ | Limited | ❌ | ❌ | ❌ |

> **Note:** This matrix is intentionally preliminary and will be refined during Step 4 (Functional Requirements).

---

## 3.18 Access Scope

Roles alone aren't enough — we also need to understand **scope**.

A user may have:

```
Role         = Manager
Organization = ACME
Team         = Engineering
Projects     = Project A + Project B
```

Their effective authorization becomes:

```
ROLE + ORGANIZATION + RESOURCE + ACTION = AUTHORIZATION DECISION
```

Conceptually: *Can user X perform action Y on resource Z within organization A?*

That question must be answered server-side.

---

## 3.19 Trust Levels

| Level | Name | Description |
|---|---|---|
| 0 | Unauthenticated | Anonymous visitor; can access public resources only |
| 1 | Authenticated User | Logged-in user; can access resources permitted to their identity and organization memberships |
| 2 | Privileged Organization User | Manager, Organization Admin — higher organizational privileges |
| 3 | Organization Owner | Highest normal organizational privilege |
| 4 | Platform Administrator | Platform-level administrative capabilities |
| 5 | System/Infrastructure Trust | Workers, scheduler, deployment infrastructure — non-human, narrowly scoped service identities |

---

## 3.20 User Lifecycle

```
Invited
   ↓
Registered
   ↓
Email Verified
   ↓
Active
   ↓
Suspended
   ↓
Deactivated
   ↓
Deleted/Anonymized
```

Exact behavior will be defined later. For example: a deactivated user should not be able to authenticate successfully even if they still know their password.

---

## 3.21 Organization Membership Lifecycle

```
Invitation Sent
       ↓
Invitation Accepted
       ↓
Active Member
       ↓
Suspended
       ↓
Removed
```

A user account can exist independently of an organization's membership. For example:

```
Alice
  │
  ├── ACME       → Active
  │
  └── Startup X  → Removed
```

Alice still has a platform account, but her Startup X membership no longer exists.

---

## 3.22 Organization Ownership

An organization must have ownership rules, including support for:

```
Owner → Transfer ownership → New Owner
```

Ownership transfers should be:

- Authenticated
- Authorized
- Audited

This is an important security-sensitive operation.

---

## 3.23 Authentication Requirements by Actor

| Actor | Requirement |
|---|---|
| Anonymous | No authentication |
| Standard User | Authentication required |
| Manager | Authentication required |
| Organization Admin | Authentication required |
| Organization Owner | Authentication required, with stronger security requirements for sensitive actions |
| Platform Administrator | Strong authentication and privileged access controls |
| API Client | Machine authentication using appropriately scoped credentials |
| Background Worker | Service identity/credential |

---

## 3.24 User Workflow — New Organization

```
User registers
      ↓
Verifies email
      ↓
Creates organization
      ↓
Becomes Organization Owner
      ↓
Invites users
      ↓
Assigns roles
      ↓
Creates teams
      ↓
Creates projects
      ↓
Begins using platform
```

---

## 3.25 User Workflow — Invitation

```
Owner/Admin
     ↓
Invite user
     ↓
Invitation created
     ↓
Notification/email
     ↓
User accepts
     ↓
Account authenticated
     ↓
Membership activated
     ↓
Role assigned
```

Every important state transition should eventually generate appropriate audit events.

---

## 3.26 User Workflow — Authorization

Every protected request should conceptually follow:

```
Request
   ↓
Authenticate identity
   ↓
Identify organization context
   ↓
Identify target resource
   ↓
Verify tenant ownership
   ↓
Determine role
   ↓
Check permission
   ↓
Perform action
   ↓
Record audit event where required
```

This workflow will become extremely important during:

- Step 6 — Threat Model
- Step 7 — Architecture
- Step 8 — Database
- Step 9 — APIs
- Step 14 — Security Testing
- Step 21 — Security Assessment

---

## 3.27 Security Principles for Users

- **Least privilege** — Users receive only the permissions they need.
- **Deny by default** — If a permission isn't explicitly granted, the result is `DENY`.
- **Server-side enforcement** — The frontend does not decide authorization.
- **Tenant isolation** — Organization boundaries are enforced server-side.
- **Separation of duties** — Highly sensitive responsibilities should not unnecessarily be concentrated in one role.
- **Auditability** — Sensitive administrative actions should be traceable.
- **Credential protection** — Authentication credentials must be protected.

---

## 3.28 Custom Roles

The platform will eventually support custom roles:

```
Organization
      │
      ├── Owner
      ├── Admin
      ├── Manager
      ├── User
      ├── Auditor
      └── Custom Security Reviewer
```

A custom role might have:

```
audit:view      = GRANTED
project:view    = GRANTED
document:view   = GRANTED

user:delete     = DENIED
billing:manage  = DENIED
role:assign     = DENIED
```

This makes the platform much closer to a real SaaS product.

---

## 3.29 External Actors and Trust Boundaries

```
                 INTERNET
                    │
                    ▼
             ┌──────────────┐
             │   FRONTEND   │
             └──────┬───────┘
                    │
             TRUST BOUNDARY
                    │
                    ▼
             ┌──────────────┐
             │   BACKEND    │
             └──────┬───────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    Database      Redis      Services
```

The browser is untrusted. The backend must never assume that user input, client-side role, client-side organization ID, or client-side permissions are trustworthy. This principle becomes central to the threat model.

---

## 3.30 Step 3 Acceptance Criteria

| ID | Question | Status |
|---|---|---|
| AC-3.1 | Who are the human users? | ✅ Defined |
| AC-3.2 | Who are the non-human actors? | ✅ Defined |
| AC-3.3 | What is each actor responsible for? | ✅ Defined |
| AC-3.4 | What can each role access? | ✅ Initial model defined |
| AC-3.5 | What are the trust boundaries? | ✅ Initial model defined |
| AC-3.6 | How does authorization work conceptually? | ✅ Defined |
| AC-3.7 | How are users created, invited, suspended and removed? | ✅ Initial lifecycle defined |
| AC-3.8 | How are organization memberships managed? | ✅ Defined |
| AC-3.9 | What security principles govern authorization? | ✅ Defined |

**Step 3 is now established.**
