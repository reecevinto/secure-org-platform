# 6. Threat Model

## 6.0 Purpose

The Secure Organization Management Platform is a multi-tenant SaaS system that will contain:

- User identities
- Authentication credentials
- Sessions
- Organizations
- Teams
- Projects
- Documents
- Permissions
- API keys
- Billing information
- Audit records
- Administrative functionality
- Application data
- Cloud infrastructure
- CI/CD systems
- Secrets

Because the platform is multi-tenant, one of the most important security properties is:

> **A user belonging to Organization A must never gain unauthorized access to resources belonging to Organization B.**

The threat model will therefore focus heavily on:

```
Identity → Authentication → Authorization → Tenant Isolation
   → Data Protection → API Security → Infrastructure Security
   → Operational Security
```

---

## 6.1 Threat Modeling Objectives

The threat model will answer:

1. What are we protecting?
2. Who might attack the system?
3. What are the attack surfaces?
4. Where are the trust boundaries?
5. What could go wrong?
6. How could an attacker exploit it?
7. What would the impact be?
8. How will we mitigate the threat?
9. How will we test the mitigation?
10. What residual risk remains?

The goal is not to claim that the system will be impossible to attack. The goal is to **systematically identify, prioritize, mitigate, and test security risks.**

---

## 6.2 Threat Modeling Methodology

We use a combination of:

### STRIDE

For systematic threat identification:

| Letter | Category |
|---|---|
| S | Spoofing |
| T | Tampering |
| R | Repudiation |
| I | Information Disclosure |
| D | Denial of Service |
| E | Elevation of Privilege |

### Risk-Based Analysis

Each important threat is evaluated based on:

- Likelihood
- Impact
- Risk

We also incorporate: abuse cases, attack paths, trust boundaries, security controls, and residual risk.

---

## 6.3 Security Objectives

| Objective | Description |
|---|---|
| **Confidentiality** | Unauthorized users must not access protected organizational data. |
| **Integrity** | Unauthorized users must not modify protected resources. |
| **Availability** | The platform should remain available despite expected failures and reasonable abuse. |
| **Authentication** | The system must correctly establish user identity. |
| **Authorization** | The system must correctly determine what an authenticated identity is allowed to do. |
| **Tenant Isolation** | Data and operations belonging to one organization must remain isolated from other organizations. |
| **Accountability** | Important security-sensitive actions must be attributable to an authenticated identity where appropriate. |
| **Resilience** | Security controls should remain effective during component failures and abnormal conditions. |

---

## 6.4 Assets

An asset is something that needs protection.

### 6.4.1 Identity Assets
- User accounts
- Email addresses
- Password hashes
- MFA configuration
- Authentication sessions
- Session identifiers
- Recovery mechanisms

### 6.4.2 Authorization Assets
- Roles
- Permissions
- Organization memberships
- Team memberships
- Access-control policies
- Authorization relationships

> These are especially sensitive because compromise could lead to privilege escalation.

### 6.4.3 Organizational Data
- Organizations
- Teams
- Projects
- Documents
- Comments
- Notifications
- Settings
- Metadata

### 6.4.4 API Assets
- API keys
- API credentials
- OAuth/token material if introduced
- Webhook credentials
- API permissions/scopes

### 6.4.5 Financial Assets

The platform is intended to support billing, so we must protect:

- Subscription information
- Billing identifiers
- Payment-provider references
- Invoices
- Billing state
- Transaction metadata

> We should avoid storing unnecessary sensitive payment-card information ourselves.

### 6.4.6 Audit Assets
- Audit events
- Security events
- Administrative actions
- Authentication events
- Authorization events

> Audit data must itself be protected because an attacker could otherwise alter evidence of malicious activity.

### 6.4.7 Infrastructure Assets

Eventually:

- Application servers
- Databases
- Object storage
- Caches
- Queues
- Containers
- Cloud resources
- DNS
- TLS certificates
- CI/CD systems
- Container registries
- Infrastructure configuration

### 6.4.8 Secrets
- Database credentials
- API secrets
- Application secrets
- Cloud credentials
- CI/CD secrets
- Encryption keys
- Third-party integration credentials

> These will be treated as high-value assets.

---

## 6.5 Threat Actors

We model different attackers rather than assuming one generic "hacker."

### TA-01 — Unauthenticated Internet Attacker

**Capabilities:** Internet access, public application access, public API access, automated requests.

**Potential goals:** Account discovery, credential attacks, API abuse, information disclosure, DoS, application exploitation.

### TA-02 — Compromised User

An attacker obtains control of a legitimate user account.

**Potential goals:** Access organizational data, steal documents, abuse permissions, steal API keys, escalate privileges, move laterally.

### TA-03 — Malicious Organization Member

A legitimate user intentionally abuses their access. This is particularly important for SaaS.

```
Normal member → Attempts to access administrator functionality
```

### TA-04 — Privileged Insider

A user with elevated privileges abuses legitimate administrative capabilities.

**Potential goals:** Modify users, modify permissions, access sensitive data, delete resources, alter configurations.

### TA-05 — Compromised API Credential

An attacker obtains an API key. Potential consequences depend on: key scope, key privileges, expiration, rotation, revocation.

### TA-06 — Supply-Chain Attacker

An attacker compromises: a dependency, a container image, the build process, a CI/CD dependency, or a third-party service.

### TA-07 — Cloud/Infrastructure Attacker

An attacker gains access to infrastructure credentials or exploits a cloud misconfiguration.

**Potential goals:** Access database, access object storage, steal secrets, modify infrastructure, deploy malicious workloads.

---

## 6.6 Trust Boundaries

Trust boundaries identify where data moves between components or security domains.

A preliminary system boundary:

```
                     INTERNET
                         │
                         ▼
                ┌─────────────────┐
                │   Web Browser   │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Reverse Proxy / │
                │ Load Balancer   │
                └────────┬────────┘
                         │
                 TRUST BOUNDARY
                         │
                         ▼
                ┌─────────────────┐
                │   Application   │
                │     API         │
                └───────┬─────────┘
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
       ┌─────────┐ ┌─────────┐ ┌─────────┐
       │Database │ │  Cache  │ │  Queue  │
       └─────────┘ └─────────┘ └─────────┘
            │
            ▼
       ┌─────────────┐
       │Object Store │
       └─────────────┘
```

This is **not yet the final architecture**. Step 6 identifies security boundaries; Step 7 will turn these concepts into the actual architecture.

---

## 6.7 Major Attack Surfaces

### Web Application
- Login
- Registration
- Password recovery
- MFA
- Dashboard
- Forms
- File uploads
- Administrative interfaces

### API
- Authentication endpoints
- User endpoints
- Organization endpoints
- Team endpoints
- Project endpoints
- Document endpoints
- Permission endpoints
- API-key endpoints
- Billing endpoints
- Audit endpoints

### Background Processing
- Job queues
- Workers
- Scheduled tasks
- Email processing
- Notifications
- Billing events
- Webhooks

### Infrastructure
- Containers
- Cloud services
- Databases
- Object storage
- Network configuration
- Secrets
- CI/CD
- Container registry

---

## 6.8 Entry Points

**External entry points:**

- HTTPS
- REST API
- Authentication endpoints
- File upload endpoints
- Webhook endpoints
- API keys
- Administrative interfaces

**Internal entry points:**

- Database connections
- Queue messages
- Worker jobs
- Cloud APIs
- Third-party integrations
- CI/CD pipelines

---

## 6.9 Primary Threat Categories

### THREAT-001 — Account Takeover

**Scenario:** An attacker obtains or guesses a user's credentials.

**Potential impact:** Unauthorized account access, data exposure, privilege abuse, API key theft.

**Controls:** Secure password hashing, MFA, rate limiting, session controls, authentication monitoring, security notifications.

**Testing:** Authentication security tests, rate-limit tests, session tests, MFA tests.

---

## 6.10 THREAT-002 — Broken Access Control

This is one of the highest-priority threats.

**Scenario:** A normal user manipulates a request to access a resource they do not own or have permission to access.

```
User A → Requests resource belonging to User B
```

**Impact:** Potential unauthorized access or modification.

**Controls:** Server-side authorization, resource ownership checks, RBAC, permission checks, tenant isolation.

**Testing:** Authorization tests will eventually be performed against every protected resource.

---

## 6.11 THREAT-003 — Cross-Tenant Data Access

This is a **P0 threat** for this platform.

**Scenario:** A user belonging to Organization A attempts to access Organization B data.

**Impact:** Potential catastrophic confidentiality breach.

**Controls:** Tenant-aware data model, authorization middleware/service, resource-level authorization, database query constraints, security testing.

**Testing:** We will explicitly test:

```
User A → Organization A → allowed
User A → Organization B → denied
```

This becomes one of our flagship security test categories.

---

## 6.12 THREAT-004 — Privilege Escalation

**Scenario:** A low-privileged user attempts to gain administrative privileges — for example, by manipulating role IDs, permission IDs, organization IDs, API requests, or administrative endpoints.

**Controls:** Server-side authorization, explicit permission checks, role hierarchy rules, administrative boundary enforcement, audit logging.

---

## 6.13 THREAT-005 — IDOR / BOLA

A user modifies an object identifier in a request. Conceptually:

```
GET /api/projects/{project_id}
```

An attacker changes the identifier to another project's identifier.

**Risk:** Unauthorized data access, unauthorized modification, cross-tenant access.

**Controls:** Authorization must validate the relationship between:

```
authenticated identity + organization + resource + requested action
```

Not merely whether the resource exists.

---

## 6.14 THREAT-006 — Session Compromise

**Potential attacks:** Session theft, session fixation, improper expiration, session reuse, insufficient invalidation.

**Controls:** Secure session design, TLS, secure cookie attributes where applicable, session expiration, session revocation, rotation.

---

## 6.15 THREAT-007 — Injection

**Potential injection classes:** SQL injection, command injection, template injection, NoSQL injection if applicable.

**Controls:** Parameterized queries, input validation, safe APIs, output encoding, least privilege.

---

## 6.16 THREAT-008 — XSS

**Potential sources:** User-generated content, document metadata, comments, notifications, administrative interfaces.

**Controls:** Output encoding, input validation, Content Security Policy, secure frontend framework practices.

---

## 6.17 THREAT-009 — CSRF

Relevant to state-changing browser operations depending on the authentication mechanism.

**Potentially affected operations:** Change password, modify settings, create resources, delete resources, change permissions, administrative actions.

Controls will be determined by the eventual authentication architecture.

---

## 6.18 THREAT-010 — Malicious File Upload

The platform supports documents — this creates an important attack surface.

**Potential threats:** Malicious files, unexpected file types, oversized files, storage abuse, content-type spoofing, malicious filenames, path traversal attempts.

**Controls:** File validation, size limits, safe filenames, isolated storage, content-type validation, access control, malware scanning where appropriate.

---

## 6.19 THREAT-011 — API Abuse

Attackers may automate requests against the API.

**Potential attacks:** Credential attacks, enumeration, resource exhaustion, endpoint abuse, automated scraping.

**Controls:** Rate limiting, request validation, authentication, authorization, monitoring, abuse detection.

---

## 6.20 THREAT-012 — API Key Compromise

If an API key is stolen:

```
Attacker → Valid API key → Authorized API access
```

**Controls:** Scoped keys, expiration, rotation, revocation, secure storage, audit logging, usage monitoring.

---

## 6.21 THREAT-013 — Secret Exposure

**Potential sources:** Git repositories, logs, CI/CD output, environment variables, container images, configuration files, developer machines.

**Controls:** Secret management, secret scanning, CI/CD controls, least privilege, log redaction.

---

## 6.22 THREAT-014 — Audit Log Tampering

An attacker with elevated access might attempt to alter evidence.

**Controls:** Restricted write access, append-oriented design, protected storage, administrative separation, monitoring.

---

## 6.23 THREAT-015 — Denial of Service

**Potential targets:** API, authentication, database, background workers, file storage.

**Controls:** Rate limiting, resource limits, timeouts, queue controls, monitoring, autoscaling where appropriate.

---

## 6.24 THREAT-016 — Dependency / Supply Chain Attack

**Potential attack path:**

```
Compromised dependency → Application build → CI/CD → Production
```

**Controls:** Dependency pinning, dependency scanning, lockfiles, SBOM, container scanning, CI security checks.

---

## 6.25 THREAT-017 — CI/CD Compromise

**Potential attack:**

```
Attacker → Compromises repository/workflow → Modifies build
   → Malicious artifact → Production
```

**Controls:** Protected branches, least-privilege CI credentials, secret protection, dependency scanning, artifact verification, pipeline security.

---

## 6.26 THREAT-018 — Cloud Misconfiguration

**Potential examples:** Public database, public object storage, excessive IAM permissions, exposed secrets, open network rules.

**Controls:** Infrastructure as Code, IAM least privilege, security scanning, configuration validation, network segmentation, continuous monitoring.

---

## 6.27 STRIDE Mapping

| STRIDE | Example Threat |
|---|---|
| Spoofing | Account takeover |
| Tampering | Unauthorized project modification |
| Repudiation | Audit-log manipulation |
| Information Disclosure | Cross-tenant access |
| Denial of Service | API/resource exhaustion |
| Elevation of Privilege | RBAC bypass |

This will expand as the architecture becomes more concrete.

---

## 6.28 Abuse Cases

Normal requirements describe legitimate behavior. Abuse cases describe what an attacker might attempt.

| ID | Abuse Case |
|---|---|
| AC-001 | A normal user attempts to access another organization's project. |
| AC-002 | A normal user attempts to grant themselves administrator privileges. |
| AC-003 | An attacker repeatedly attempts authentication. |
| AC-004 | A compromised API key is used to access organizational resources. |
| AC-005 | A user attempts to upload a malicious or prohibited file. |
| AC-006 | An attacker attempts to enumerate organization resources. |
| AC-007 | An attacker attempts to manipulate API object identifiers. |
| AC-008 | A compromised CI/CD credential is used to modify a production deployment. |

---

## 6.29 Risk Rating

```
Likelihood × Impact = Risk
```

**Likelihood**

| Score | Meaning |
|---|---|
| 1 | Rare |
| 2 | Unlikely |
| 3 | Possible |
| 4 | Likely |
| 5 | Almost Certain |

**Impact**

| Score | Meaning |
|---|---|
| 1 | Negligible |
| 2 | Minor |
| 3 | Moderate |
| 4 | Major |
| 5 | Severe |

**Risk**

| Score Range | Rating |
|---|---|
| 1–4 | Low |
| 5–9 | Medium |
| 10–16 | High |
| 17–25 | Critical |

---

## 6.30 Initial Risk Register

| ID | Threat | Likelihood | Impact | Initial Risk |
|---|---|---|---|---|
| T-001 | Account Takeover | 4 | 5 | Critical |
| T-002 | Broken Access Control | 4 | 5 | Critical |
| T-003 | Cross-Tenant Access | 3 | 5 | High |
| T-004 | Privilege Escalation | 3 | 5 | High |
| T-005 | IDOR/BOLA | 4 | 5 | Critical |
| T-006 | Session Compromise | 3 | 5 | High |
| T-007 | Injection | 3 | 5 | High |
| T-008 | XSS | 3 | 4 | High |
| T-009 | CSRF | 3 | 4 | High |
| T-010 | Malicious File Upload | 3 | 4 | High |
| T-011 | API Abuse | 4 | 4 | High |
| T-012 | API Key Compromise | 3 | 5 | High |
| T-013 | Secret Exposure | 3 | 5 | High |
| T-014 | Audit Tampering | 2 | 4 | Medium |
| T-015 | Denial of Service | 3 | 4 | High |
| T-016 | Supply Chain Attack | 2 | 5 | Medium |
| T-017 | CI/CD Compromise | 2 | 5 | Medium |
| T-018 | Cloud Misconfiguration | 3 | 5 | High |

These are initial design-time assessments. Once the actual architecture, data flows, deployment model, and implementation exist, the risks will be reassessed.

---

## 6.31 Security Control Strategy

Our security architecture uses **defense in depth**:

```
Internet
   ↓
TLS
   ↓
Reverse Proxy / Edge Controls
   ↓
Rate Limiting
   ↓
Authentication
   ↓
Authorization
   ↓
Tenant Isolation
   ↓
Input Validation
   ↓
Business Logic Controls
   ↓
Database Controls
   ↓
Audit Logging
   ↓
Monitoring
   ↓
Security Testing
```

No single control should be considered sufficient by itself.

---

## 6.32 Threat-to-Control Traceability

Every significant threat should eventually map to:

```
Threat → Requirement → Architecture Decision → Implementation
   → Automated Test → Security Test → Operational Control
```

**Example:**

```
Cross-Tenant Access
        ↓
NFR-SEC-004
        ↓
Tenant Isolation Architecture
        ↓
Authorization Implementation
        ↓
Integration Tests
        ↓
Security Tests
        ↓
Monitoring / Audit
```

This traceability is one of the things that will make the project substantially stronger than a typical portfolio CRUD application.

---

## 6.33 Residual Risk

Security controls reduce risk; they do not eliminate it completely. After mitigation, we will document:

```
Initial Risk → Mitigation → Residual Risk → Acceptance / Further Treatment
```

**Example:**

```
Threat:          API abuse
Initial Risk:    High
Controls:        Rate limiting, Authentication, Monitoring, Request validation
Residual Risk:   Medium
Treatment:       Continuous monitoring and tuning
```

---

## 6.34 Threat Model Boundaries

The initial threat model covers:

```
Users → Web Application → API → Application Services → Database
   → Storage → Background Jobs → Third-Party Integrations
   → CI/CD → Cloud Infrastructure
```

This boundary will be refined during architecture design.

---

## 6.35 Security Testing Derived From the Threat Model

The threat model directly determines future security tests. We will eventually test:

- Authentication
- Authorization
- RBAC
- Tenant Isolation
- IDOR/BOLA
- Privilege Escalation
- Session Security
- Input Validation
- Injection
- XSS
- CSRF
- File Upload Security
- API Abuse
- API Key Security
- Secret Exposure
- Audit Integrity
- Cloud Configuration
- CI/CD Security
- Dependency Security
- Container Security

> **We are not going to randomly run security tools at the end of the project.** The threat model tells us what we need to test and why.

---

## 6.36 Step 6 Deliverables

| Deliverable | Status |
|---|---|
| Threat modeling methodology | ✅ |
| Security objectives | ✅ |
| Asset inventory | ✅ |
| Threat actor inventory | ✅ |
| Trust boundaries | ✅ |
| Attack surface | ✅ |
| Entry points | ✅ |
| Threat catalog | ✅ |
| STRIDE analysis | ✅ |
| Abuse cases | ✅ |
| Attack scenarios | ✅ |
| Risk methodology | ✅ |
| Initial risk register | ✅ |
| Security controls | ✅ |
| Mitigation strategy | ✅ |
| Threat-to-control traceability | ✅ |
| Residual risk methodology | ✅ |
| Security testing requirements | ✅ |

**Step 6 is now established.**
