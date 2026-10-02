# Automation

Programmatic interfaces to Fortinet products: REST API, Ansible, Terraform, FortiManager scripts, FortiSOAR connectors, Python libraries. The right automation choice depends on whether the user wants **idempotent infrastructure-as-code** (Terraform), **declarative configuration management** (Ansible), **device-level scripting** (FortiManager), or **operational orchestration** (FortiSOAR / Python + REST).

## Table of contents

1. Decision matrix — picking the right tool
2. FortiOS REST API
3. FortiManager API and scripts
4. FortiAnalyzer / FortiSIEM API
5. Ansible (fortinet collections)
6. Terraform (Fortinet provider)
7. FortiSOAR — playbook engine
8. Python libraries (FortiOSAPI, pyFortiAPI, fmgr-jsonrpc)
9. Authentication, secrets, and CI/CD posture
10. Idempotency, drift, and rollback patterns
11. Testing and validation

---

## 1. Decision matrix

| Need | Tool of choice | Why |
|---|---|---|
| Provision new FortiGate-VM in cloud (AWS/Azure/GCP) | Terraform | True IaC, state tracking, plan/apply, version-controlled |
| Standardize FortiGate config across many devices | FortiManager + provisioning templates / Ansible | Manager workflow + ADOM separation; Ansible if no FortiManager |
| One-off operational change at scale (e.g., update DNS) | Ansible | Declarative, idempotent, parallel, dry-run via check mode |
| Custom CMDB integration / event-driven response | Python + REST API | Maximum flexibility; ties into customer toolchains |
| Incident response orchestration | FortiSOAR | Playbook engine + connector framework + case management |
| Bulk policy edits via UI is too slow | FortiManager scripts (CLI scripts in ADOM) | Native, version-controlled in FortiManager |
| Reporting / dashboarding | FortiAnalyzer reports + FortiSOAR + custom API | Native first; custom only if native gaps |

---

## 2. FortiOS REST API

### Authentication

Two primary methods:

- **API administrator with API key** — the recommended path. Create an `api_admin` user with an API key bound to a trusted-host source IP. API key is sent as `Authorization: Bearer <token>` or `?access_token=<token>` (query string is less secure; use header).
- **Username/password session** — works but discouraged for automation. Each call opens/closes a session; CSRF token handling adds complexity.

```python
import requests

session = requests.Session()
session.headers.update({
    "Authorization": "Bearer <api_token>",
    "Content-Type": "application/json"
})
session.verify = "/path/to/ca-bundle.pem"  # never disable SSL verify in prod

base = "https://fortigate.example.com/api/v2"
```

### Endpoint shape

REST API endpoints follow:
```
/api/v2/<scope>/<object-type>/<object-id>
```

Scopes:
- `cmdb` — configuration (read/write)
- `monitor` — operational state (typically read)
- `log` — log queries

Examples:
```
GET  /api/v2/cmdb/firewall/policy
GET  /api/v2/cmdb/firewall/policy/12
PUT  /api/v2/cmdb/firewall/policy/12
POST /api/v2/cmdb/firewall/address
DELETE /api/v2/cmdb/firewall/address/<name>

GET  /api/v2/monitor/system/status
GET  /api/v2/monitor/router/ipv4
GET  /api/v2/monitor/firewall/session
```

VDOM scoping: pass `?vdom=<vdom-name>` or `?vdom=root`.

### Patterns

- **Read-modify-write**: GET the object, modify, PUT it back. Some objects are tricky — use the docs for the specific schema.
- **Bulk operations**: prefer batch where supported; for true bulk policy edits at scale, consider FortiManager script over per-call API.
- **Rate limiting**: not strict, but a busy FortiGate doing live traffic will not appreciate thousands of API calls per second. Throttle.
- **Response codes**: 200 success, 4xx config errors (read the body for the actual message), 5xx server-side. The body's `status`, `http_status`, and `error` fields tell you what actually happened.

### Reference

Full API reference per FortiOS version:
```
docs.fortinet.com/document/fortigate/<version>/rest-api-reference/...
```

Always use the version-matching reference. The schema evolves between versions.

---

## 3. FortiManager API and scripts

### JSON-RPC API

FortiManager exposes a JSON-RPC API rather than REST:
```
POST https://fortimanager.example.com/jsonrpc
```

Body shape:
```json
{
  "id": 1,
  "method": "exec",
  "params": [
    {
      "url": "/sys/login/user",
      "data": {"user": "<user>", "passwd": "<password>"}
    }
  ]
}
```

After login, subsequent calls use the returned session token.

The API is powerful but verbose — common operations involve multiple round-trips. Python libraries (e.g., `fmgr-jsonrpc`, `pyFMG`) wrap this.

### FortiManager scripts

CLI scripts attached to ADOMs can be applied to one or many devices. Useful for:
- Bulk policy edits
- Standardizing per-site config additions (e.g., "add this admin user to every site")
- Provisioning workflows where the same script runs on each new device

Scripts are stored in the FortiManager, version-controlled within the platform, and visible in the audit trail.

### Provisioning templates

For larger fleets, FortiManager provisioning templates handle:
- Interface assignments
- System settings
- SNMP, syslog, NTP
- AAA
- Certificates

These are layered on top of policy packages. Misalignment between provisioning template and policy package is a common deployment surprise — keep them coherent.

---

## 4. FortiAnalyzer / FortiSIEM API

### FortiAnalyzer

Same JSON-RPC pattern as FortiManager. Common operations:
- Query logs
- Run reports
- Manage devices/ADOMs
- Pull events

Useful for SIEM-style integrations where customer wants to ingest FortiAnalyzer data into another platform.

### FortiSIEM

FortiSIEM has its own API (REST-based) for:
- Event/incident retrieval
- Rule management
- CMDB queries
- User/role management

For external SIEM integration (Splunk, QRadar, etc.), more common pattern is syslog forwarding from FortiAnalyzer/FortiGate directly to the external SIEM rather than API-pulling from FortiSIEM.

---

## 5. Ansible

Fortinet maintains official collections on Ansible Galaxy:

- `fortinet.fortios` — FortiGate (FortiOS)
- `fortinet.fortimanager` — FortiManager
- `fortinet.fortianalyzer` — FortiAnalyzer
- `fortinet.fortiswitch` — FortiSwitch (standalone)
- `fortinet.fortiweb` — FortiWeb
- `fortinet.fortiadc` — FortiADC
- (verify currency on Ansible Galaxy and Fortinet docs — collections evolve)

### Inventory

For FortiGate, inventory is typically:
```yaml
all:
  hosts:
    fgt-site-a:
      ansible_host: 10.0.0.1
      ansible_user: api_admin
      ansible_password: "{{ vault_fgt_token }}"
      ansible_network_os: fortinet.fortios.fortios
      ansible_httpapi_use_ssl: yes
      ansible_httpapi_validate_certs: yes
      ansible_httpapi_port: 443
```

For API-key auth (preferred):
```yaml
ansible_user: ""
ansible_password: ""
ansible_httpapi_use_proxy: no
# token in module-level argument or via env var
```

### Module pattern

```yaml
- name: Ensure firewall address exists
  fortinet.fortios.fortios_firewall_address:
    vdom: "root"
    state: "present"
    firewall_address:
      name: "office-prefix"
      type: "ipmask"
      subnet: "10.10.0.0 255.255.0.0"
      comment: "Site A office subnet"
```

### Idempotency

Modules are designed to be idempotent — running twice should produce the same result with `changed: false` on the second run. Test this on a non-prod device first; some modules have quirks where ordering matters or where empty-vs-default fields trigger spurious changes.

### Common pitfalls

- **VDOM mismatch** — module-level `vdom` parameter must match the VDOM the object lives in
- **Reference order** — creating a policy that references an address must be in the correct order; Ansible plays handle this with task ordering
- **Whitespace in CLI lists** — Fortinet's CLI sometimes treats leading/trailing whitespace differently; the API normalizes this but watch for round-trip drift
- **Schema drift between versions** — pinning the collection version is essential for reproducibility

---

## 6. Terraform

Fortinet maintains official providers:

- `fortinetdev/fortios` — FortiGate (FortiOS, the most-used)
- `fortinetdev/fortimanager` — FortiManager
- `fortinetdev/fortianalyzer` — FortiAnalyzer
- (and others — verify on Terraform Registry)

### Provider config

```hcl
terraform {
  required_providers {
    fortios = {
      source  = "fortinetdev/fortios"
      version = "~> 1.x.x"   # pin minor, allow patch
    }
  }
}

provider "fortios" {
  hostname = var.fortigate_host
  token    = var.fortigate_api_token
  insecure = false
  cabundlefile = "/path/to/ca.pem"
}
```

### Resource pattern

```hcl
resource "fortios_firewall_address" "office" {
  name    = "office-prefix"
  type    = "ipmask"
  subnet  = "10.10.0.0 255.255.0.0"
  comment = "Site A office subnet"
}

resource "fortios_firewall_policy" "allow_office_to_internet" {
  policyid = 100
  name     = "Office to Internet"
  srcintf {
    name = "internal"
  }
  dstintf {
    name = "wan1"
  }
  srcaddr {
    name = fortios_firewall_address.office.name
  }
  dstaddr {
    name = "all"
  }
  service {
    name = "ALL"
  }
  action  = "accept"
  status  = "enable"
  schedule = "always"
  nat     = "enable"
}
```

### When Terraform shines

- Cloud FortiGate-VM provisioning end-to-end (compute + FortiOS config in one plan)
- Multi-environment parity (dev/stage/prod with the same code)
- Drift detection (`terraform plan` shows what changed out-of-band)

### When Terraform struggles

- Ordering-sensitive operations on existing live devices (state vs reality reconciliation can be ugly)
- Operations that aren't truly declarative (one-shot diagnostic actions)
- Mass operations across hundreds of disparate FortiGates with frequent ad-hoc changes — Ansible or FortiManager is often a better fit

### State management

Use remote state (S3, Terraform Cloud, etc.) with locking. For multi-engineer environments, never use local state.

---

## 7. FortiSOAR

Playbook-driven security orchestration. Built on Python (the underlying engine) with a visual playbook builder. Connects to a wide range of products via the Connector framework (Fortinet + third-party).

### Architecture

- **Playbooks** — workflows triggered by events, manual action, or schedule
- **Connectors** — integrations with products (read/write to other platforms via their APIs)
- **Records** — alerts, incidents, indicators, etc., flowing through the platform
- **Modules** — customer-extensible data models

### When to choose FortiSOAR

- Customer needs incident-response orchestration with case management
- Multi-product investigation/response automation (EDR + SIEM + email + identity + tickets)
- Repeatable response patterns the SOC wants to encode
- Regulatory or audit requirements for documented response workflows

### Building custom connectors

Python-based. Useful for customer-specific integrations not in the existing connector catalog. The Connector SDK (Fortinet documentation) covers structure, action handlers, schema definition.

---

## 8. Python libraries (community / Fortinet)

Several Python libraries wrap the Fortinet APIs:

- **FortiOSAPI** — Fortinet-published, covers FortiOS REST
- **pyFortiAPI** — community library, lighter weight
- **fmgr-jsonrpc** — for FortiManager
- **pyFMG** — older but widely used FortiManager wrapper
- **forti-tooling** ecosystem — various community tools

For new automation work, prefer:
- **FortiOSAPI** (Fortinet-maintained) for FortiOS
- **Direct `requests`** when you need full control and the wrapper adds friction
- **Ansible / Terraform** when the task is truly declarative

For one-off operational scripts, direct `requests` calls are often simpler than wrapping in a library.

---

## 9. Authentication, secrets, and CI/CD posture

### Secrets

- API tokens belong in a secrets manager (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
- For Ansible: Ansible Vault for low-friction; integration with external secrets manager for higher-security
- For Terraform: provider config takes tokens from variables; populate from secrets manager via Terraform Cloud or CI/CD environment
- **Never** commit tokens to source control. Treat token leak the same as credential leak — rotate immediately.

### Trusted hosts

API admins must have a `trusthost` configured (limit source IPs). Without trusthost, the API admin is reachable from anywhere — significant exposure.

```fortios
config system api-user
  edit "automation_admin"
    set api-key ENC <token>
    set trusthost1 192.0.2.0 255.255.255.0
    set trusthost2 198.51.100.0 255.255.255.0
  next
end
```

### CI/CD considerations

- **Plan in PR**, **apply on merge** — standard Terraform pattern
- **Automated testing on a non-prod FortiGate-VM** before merging to main
- **Approval gates** for production changes — match the customer's change-management discipline
- **Rollback strategy** — Terraform: revert the commit and apply; Ansible: maintain a baseline playbook to restore last-known-good; FortiManager: use config revisions

---

## 10. Idempotency, drift, and rollback

### Idempotency

A correctly idempotent automation tool produces the same end state regardless of how many times it runs. Test this:
1. Run once → check changes
2. Run again immediately → expect zero changes
3. Manually modify the FortiGate → run again → expect changes back to declared state

If step 2 reports changes, the tool isn't idempotent for that resource — usually a schema-mismatch or default-value issue.

### Drift detection

Manual changes on a FortiGate (CLI) drift from declared state. Detection patterns:
- Terraform `plan` shows out-of-band changes
- FortiManager out-of-sync detection
- Periodic `git diff` of exported configs

Drift is normal in dynamic environments — what matters is having a process to either (a) reconcile drift back to declared state, or (b) accept the drift into the declared state.

### Rollback

Plan rollback **before** applying. For complex changes:
- Snapshot config before change (`execute backup config flash <slot>`)
- Document the exact rollback command sequence
- Test rollback on a non-prod first when feasible

For HA pairs, change one unit, validate, then change the other — preserves a known-good fallback.

---

## 11. Testing and validation

### Unit / module tests

- Ansible: `molecule` framework for testing roles
- Terraform: `terraform validate` for syntax, `terraform plan` for change preview, `terratest` for integration testing on real (or VM) FortiGates

### Integration tests

Run against a non-prod FortiGate-VM:
- Spin up FG-VM in cloud or on-prem hypervisor
- Apply automation
- Validate end state via separate read-only queries
- Tear down

### Pre-prod validation

For high-stakes changes:
1. Apply in lab → validate
2. Apply in pilot site → validate over time window
3. Apply across fleet in waves
4. Monitor for anomalies between waves

This is operational discipline more than tooling — but the tooling enables it.

---

## Common automation deliverables

For a presales conversation about automation:
- "Show me automation for FortiGate" → demo Terraform (cloud) + Ansible (config) + a FortiSOAR playbook
- "How do I integrate with our existing CI/CD?" → Terraform/Ansible in their pipeline + secrets manager wiring
- "Can we move to GitOps for firewall policy?" → yes, via FortiManager + FortiManager-as-source-of-truth + git for FortiManager scripts
- "What about ChatOps?" → FortiSOAR connectors for Slack/Teams + playbooks triggered from chat

For implementation deliverables:
- A working Terraform module with module-level documentation
- An Ansible role/collection with example playbooks
- A FortiManager workflow doc explaining template/policy-package separation
- A FortiSOAR playbook with a clear input/output contract

For each, include: schema version, FortiOS version compatibility, dependencies, idempotency confirmation, rollback path.
