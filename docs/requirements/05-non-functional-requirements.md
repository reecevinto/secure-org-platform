# 5. Non-Functional Requirements

This step is extremely important for turning this from a school-style CRUD application into something we can legitimately describe as a production-grade engineering project.

Functional requirements tell us **what the platform does**. Non-functional requirements tell us **how well, how securely, how reliably, and under what operational conditions** it must do it.

**Example:**

```
Functional:
The API shall allow users to retrieve projects.

Non-functional:
The API should return normal project retrieval requests
within an agreed latency target under the defined load.
```

The second requirement changes how we architect, test, deploy, monitor, and scale the system.

---

## 5.1 Non-Functional Requirement Categories

1. Security
2. Performance
3. Availability
4. Reliability
5. Scalability
6. Maintainability
7. Observability
8. Resilience
9. Disaster Recovery
10. Data Integrity
11. Privacy
12. Usability
13. Accessibility
14. Compatibility
15. Portability
16. Deployability
17. Testability
18. Operability
19. Auditability
20. Resource Efficiency

Requirements are given measurable targets wherever it makes sense.

---

## 5.2 Requirement Priority

| Priority | Meaning |
|---|---|
| P0 | Critical |
| P1 | High |
| P2 | Medium |
| P3 | Future |

We also introduce a second attribute — **Target** — because a production requirement should ideally be measurable.

---

## 5.3 Security

Security is one of the defining characteristics of this project.

| ID | Requirement | Priority |
|---|---|---|
| NFR-SEC-001 | **Secure Authentication** — The system shall implement authentication using industry-accepted security practices. | P0 |
| NFR-SEC-002 | **Password Protection** — Passwords shall never be stored in plaintext. Passwords shall be processed using a modern password-hashing algorithm designed for password storage. | P0 |
| NFR-SEC-003 | **Authorization** — All protected operations shall undergo server-side authorization. Client-side authorization controls shall not be considered sufficient. | P0 |
| NFR-SEC-004 | **Tenant Isolation** — The system shall enforce logical isolation between organizations. A user authorized within one organization shall not be able to access another organization's resources unless explicitly authorized. | P0 |
| NFR-SEC-005 | **Least Privilege** — Application components, service accounts, users, and infrastructure resources shall operate with the minimum privileges required. | P0 |
| NFR-SEC-006 | **Secure Secrets** — Secrets shall not be committed to source control. Production secrets shall be supplied through appropriate secret-management mechanisms. | P0 |
| NFR-SEC-007 | **Transport Security** — Production application traffic shall use encrypted transport. *Target: HTTPS/TLS* | P0 |
| NFR-SEC-008 | **Input Validation** — All externally supplied input shall be validated and handled safely. | P0 |
| NFR-SEC-009 | **Rate Limiting** — Authentication, API, and other abuse-sensitive operations shall implement appropriate rate limiting. | P1 |
| NFR-SEC-010 | **Security Headers** — Production HTTP responses shall implement appropriate security headers. | P1 |
| NFR-SEC-011 | **Dependency Security** — Third-party dependencies shall be periodically assessed for known security vulnerabilities. | P1 |
| NFR-SEC-012 | **Security Logging** — Security-sensitive events shall generate appropriate audit or security telemetry. | P1 |

---

## 5.4 Performance

We need actual targets — but we should not invent unrealistic enterprise performance claims just to make the project sound impressive. Initial engineering targets are established here and validated through testing.

| ID | Requirement |
|---|---|
| NFR-PERF-001 | **API Latency** — For normal authenticated API requests under the defined baseline workload. *Target: p95 latency ≤ 500 ms* (measured, not merely claimed) |
| NFR-PERF-002 | **Authentication** — Authentication operations should complete within an acceptable interactive response time under normal load. |
| NFR-PERF-003 | **Database Queries** — Normal application queries should avoid unnecessary full-table scans and excessive database round trips. |
| NFR-PERF-004 | **Frontend Responsiveness** — Normal user interactions should provide responsive feedback without unnecessary blocking operations. |
| NFR-PERF-005 | **Background Processing** — Long-running operations should be moved to asynchronous processing where appropriate. |

---

## 5.5 Availability

Availability defines how often the service should be usable.

**NFR-AVL-001** — The production system should target **99.5% monthly availability** for the initial deployment.

Why not immediately claim 99.99%? Because we are building the system and infrastructure ourselves — we need to earn the number through operational evidence. Later, once the architecture and operational model mature, a higher target can be established.

---

## 5.6 Reliability

| ID | Requirement |
|---|---|
| NFR-REL-001 | The system shall handle expected application failures without corrupting persistent data. |
| NFR-REL-002 | Transient failures in external dependencies shall be handled using appropriate retry behavior where safe. |
| NFR-REL-003 | Background jobs shall support controlled retry behavior. |
| NFR-REL-004 | Failed background jobs shall be observable. |
| NFR-REL-005 | The system shall provide health and readiness checks. |
| NFR-REL-006 | Critical operations shall be designed to avoid unintended duplicate processing where possible. |

> **NFR-REL-006 will become particularly important for:** payments, emails, background jobs, webhooks.

---

## 5.7 Scalability

| ID | Requirement |
|---|---|
| NFR-SCALE-001 | The application architecture shall support horizontal scaling of stateless application instances. |
| NFR-SCALE-002 | The application shall avoid unnecessary dependence on local application-instance state. |
| NFR-SCALE-003 | Background workloads shall support independent worker scaling. |
| NFR-SCALE-004 | Database access shall use controlled connection management. |
| NFR-SCALE-005 | Object storage shall be used for appropriate large-file storage rather than unnecessarily storing large binary objects directly inside relational tables. |

---

## 5.8 Maintainability

This is critical for demonstrating software engineering maturity.

| ID | Requirement |
|---|---|
| NFR-MAINT-001 | The codebase shall follow consistent formatting and style standards. |
| NFR-MAINT-002 | The project shall use automated linting and formatting. |
| NFR-MAINT-003 | The codebase shall be modular and organized around clear responsibilities. |
| NFR-MAINT-004 | Business logic shall not be unnecessarily coupled to infrastructure concerns. |
| NFR-MAINT-005 | Important architectural decisions shall be documented. |
| NFR-MAINT-006 | Dependencies shall be version-controlled. |

---

## 5.9 Observability

The system should eventually expose three major telemetry categories: **logs, metrics, traces**.

| ID | Requirement |
|---|---|
| NFR-OBS-001 | Application logs shall be structured. |
| NFR-OBS-002 | Logs shall contain sufficient contextual information for troubleshooting without unnecessarily exposing sensitive data. |
| NFR-OBS-003 | The system shall expose application and infrastructure metrics. |
| NFR-OBS-004 | The system shall support distributed tracing where appropriate. |
| NFR-OBS-005 | Operational dashboards shall provide visibility into service health. |
| NFR-OBS-006 | Critical service failures shall generate actionable alerts. |

---

## 5.10 Resilience

The system should continue operating when individual components experience failure.

| ID | Requirement |
|---|---|
| NFR-RES-001 | Failure of a non-critical background task shall not unnecessarily make the primary application unavailable. |
| NFR-RES-002 | External service failures shall be handled gracefully. |
| NFR-RES-003 | The system shall implement appropriate timeouts for network dependencies. |
| NFR-RES-004 | The application shall prevent uncontrolled retry storms. |

> **This will become important when designing:** API clients, workers, queues, external services.

---

## 5.11 Disaster Recovery

This is where the project starts entering real SRE territory. We need: backup, recovery, and recovery testing.

| ID | Requirement |
|---|---|
| NFR-DR-001 | Critical persistent data shall be backed up according to the defined backup strategy. |
| NFR-DR-002 | Backups shall be protected against unauthorized access. |
| NFR-DR-003 | The system shall define a Recovery Point Objective. *Initial target: RPO ≤ 24 hours* |
| NFR-DR-004 | The system shall define a Recovery Time Objective. *Initial target: RTO ≤ 4 hours* |

These are initial targets, not claims that we already meet them — they will be tested later.

---

## 5.12 Data Integrity

| ID | Requirement |
|---|---|
| NFR-DATA-001 | The system shall maintain referential integrity for relational data. |
| NFR-DATA-002 | Critical operations shall use appropriate transactional guarantees. |
| NFR-DATA-003 | The system shall prevent unauthorized modification of protected audit records. |
| NFR-DATA-004 | Data validation shall occur at appropriate application and database boundaries. |

---

## 5.13 Privacy

| ID | Requirement |
|---|---|
| NFR-PRIV-001 | The system shall minimize unnecessary collection of personal information. |
| NFR-PRIV-002 | Sensitive information shall not be unnecessarily exposed in logs. |
| NFR-PRIV-003 | Access to user data shall follow authorization controls. |
| NFR-PRIV-004 | The system shall support appropriate data retention and deletion mechanisms. |

---

## 5.14 Usability

Security shouldn't make the platform unusable.

| ID | Requirement |
|---|---|
| NFR-USE-001 | Common workflows shall require a reasonable number of user interactions. |
| NFR-USE-002 | The interface shall provide clear feedback for successful and failed operations. |
| NFR-USE-003 | Validation errors shall provide actionable information without exposing sensitive implementation details. |
| NFR-USE-004 | Security-sensitive actions shall clearly communicate their consequences. |

---

## 5.15 Accessibility

| ID | Requirement |
|---|---|
| NFR-ACC-001 | The frontend should follow recognized accessibility practices. *Target: WCAG 2.2 AA, where practical* |
| NFR-ACC-002 | The interface should support keyboard navigation. |
| NFR-ACC-003 | Interactive elements should have appropriate accessible names. |
| NFR-ACC-004 | The application should maintain sufficient visual contrast. |

---

## 5.16 Compatibility

The web application should support current major browsers.

**Initial target:** Chrome, Edge, Firefox, Safari.

We don't need to support legacy browsers.

---

## 5.17 Portability

| ID | Requirement |
|---|---|
| NFR-PORT-001 | The application shall be containerized. |
| NFR-PORT-002 | The application should avoid unnecessary dependency on a single cloud provider where practical. |
| NFR-PORT-003 | Infrastructure configuration shall be reproducible. |

---

## 5.18 Deployability

| ID | Requirement |
|---|---|
| NFR-DEP-001 | Application builds shall be reproducible. |
| NFR-DEP-002 | Deployments shall be automated through CI/CD. |
| NFR-DEP-003 | Production deployments shall not depend on manually modifying application servers. |
| NFR-DEP-004 | Infrastructure shall be defined through Infrastructure as Code. |
| NFR-DEP-005 | Deployment failures shall be detectable. |

---

## 5.19 Testability

This is extremely important.

| ID | Requirement |
|---|---|
| NFR-TEST-001 | The system shall support automated unit testing. |
| NFR-TEST-002 | The system shall support integration testing. |
| NFR-TEST-003 | The system shall support end-to-end testing. |
| NFR-TEST-004 | Security-sensitive functionality shall have dedicated security tests. |
| NFR-TEST-005 | Critical application behavior shall have automated regression coverage. |
| NFR-TEST-006 | The CI/CD pipeline shall execute appropriate automated tests before deployment. |

---

## 5.20 Operability

The system should be manageable by an engineer who did not originally write it.

| ID | Requirement |
|---|---|
| NFR-OPS-001 | The system shall provide health information. |
| NFR-OPS-002 | Operational configuration shall be externalized where appropriate. |
| NFR-OPS-003 | Deployment procedures shall be documented. |
| NFR-OPS-004 | Incident response procedures shall eventually be documented. |
| NFR-OPS-005 | Operational runbooks shall be created for important failure scenarios. |

---

## 5.21 Auditability

| ID | Requirement |
|---|---|
| NFR-AUDIT-001 | Security-sensitive administrative operations shall be auditable. |
| NFR-AUDIT-002 | Audit records shall contain sufficient context to reconstruct important security events. |
| NFR-AUDIT-003 | Audit logs shall be protected against unauthorized modification. |
| NFR-AUDIT-004 | Audit data shall be retained according to defined retention policies. |

---

## 5.22 Resource Efficiency

| ID | Requirement |
|---|---|
| NFR-RESRC-001 | The application shall avoid unnecessary resource consumption. |
| NFR-RESRC-002 | Background workers shall not continuously consume resources when no work is available. |
| NFR-RESRC-003 | Database queries shall be optimized before scaling infrastructure unnecessarily. |
| NFR-RESRC-004 | Cloud resources shall be monitored for unnecessary utilization. |

> **This will eventually connect directly to FinOps and cloud cost management.**

---

## 5.23 Initial Performance Targets

| Metric | Initial Target |
|---|---|
| API p95 latency | ≤ 500 ms |
| Availability | ≥ 99.5% |
| RPO | ≤ 24 hours |
| RTO | ≤ 4 hours |
| Automated deployment | Required |
| Containerized deployment | Required |
| HTTPS production traffic | Required |
| Critical security tests | Required |
| Structured logging | Required |
| Health checks | Required |
| Horizontal scaling capability | Required |

These are engineering targets, not marketing claims. Once the system exists, it will be benchmarked against them.

---

## 5.24 Environment-Specific Requirements

One mistake to avoid is pretending development and production are identical. Three primary environments are defined:

```
Development → Staging → Production
```

**Development** — Optimized for developer productivity, debugging, rapid iteration.

**Staging** — Optimized for production-like validation, integration testing, security testing, deployment testing.

**Production** — Optimized for availability, security, performance, observability, reliability.

---

## 5.25 Security vs. Performance

There will sometimes be trade-offs. For example:

```
More password hashing work → Stronger password security → More CPU usage
```

```
More logging → Better observability → More storage/cost
```

Engineering decisions should explicitly consider these trade-offs rather than blindly optimizing one metric. This becomes particularly valuable when architecture decision records are created later.

---

## 5.26 Non-Functional Requirement Traceability

| NFR | Design Area | Test |
|---|---|---|
| NFR-SEC-004 | Tenant isolation architecture | Security test |
| NFR-PERF-001 | API architecture | Load test |
| NFR-AVL-001 | Cloud architecture | Availability monitoring |
| NFR-DR-003 | Backup architecture | Recovery test |
| NFR-OBS-001 | Logging architecture | Observability test |
| NFR-DEP-002 | CI/CD | Deployment test |
| NFR-TEST-001 | Testing architecture | CI pipeline |
| NFR-ACC-001 | Frontend | Accessibility test |

This matrix will be populated as implementation progresses.

---

## 5.27 Step 5 Acceptance Criteria

| Item | Status |
|---|---|
| Security requirements | ✅ |
| Performance requirements | ✅ |
| Availability requirements | ✅ |
| Reliability requirements | ✅ |
| Scalability requirements | ✅ |
| Maintainability requirements | ✅ |
| Observability requirements | ✅ |
| Resilience requirements | ✅ |
| Disaster recovery requirements | ✅ |
| Data integrity requirements | ✅ |
| Privacy requirements | ✅ |
| Usability requirements | ✅ |
| Accessibility requirements | ✅ |
| Compatibility requirements | ✅ |
| Portability requirements | ✅ |
| Deployment requirements | ✅ |
| Testability requirements | ✅ |
| Operability requirements | ✅ |
| Auditability requirements | ✅ |
| Resource efficiency requirements | ✅ |
| Initial measurable targets | ✅ |

**Step 5 is now established.**
