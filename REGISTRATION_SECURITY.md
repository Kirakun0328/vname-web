# Registration security operations

## Implemented controls
- Receipt capability required for private status and deletion; public status-by-account endpoint disabled.
- Public response allowlist omits receipt secrets and exact submission times.
- IP rate-limit identifiers use an environment-held HMAC key and hourly scope, in a separate table.
- Expired limits and unapproved submissions older than 90 days are deleted on authenticated scheduled queue reads and valid new submissions. The existing review workflow runs on a five-minute schedule; GitHub can delay or stop scheduled jobs. Monitor job failures. Approved records remain until removal.
- JSON size and read-time limits; exact source host allowlists; HTML rendered as text by consumers; frame denial and restrictive browser permissions.
- Review decisions require signed, short-lived GitHub OIDC credentials scoped to the expected repository, branch and workflow.
- The review process receives only required environment variables. Checkout does not retain Git credentials. Authenticated HTTP calls refuse redirects.

## Incident procedure
1. Set Sites runtime REGISTRATIONS_PAUSED=true and redeploy the saved version to stop new POST requests. DELETE remains available. Status POST is also paused. This does not disable public listing.
2. If listing integrity or ongoing data exposure is suspected, restrict the Site audience in Sites settings and notify users. This also interrupts public registration lookup from the main site; the main bundled dictionary remains separate.
3. Revoke compromised editor access and account sessions in GitHub and Sites. Enable strong MFA/passkeys for operator accounts. These account settings require the owner and are not configured by this code change.
4. Rotate REGISTRATION_RATE_SECRET through Sites secrets and redeploy. Review short-lived source credentials and GitHub workflow permissions. Do not put secrets in source or incident tickets.
5. Contact the hosting provider for log retention, log redaction, deletion and backup handling. Current tools do not expose those settings. Preserve only the minimum evidence needed; do not publish raw logs, IPs or tokens.
6. Identify affected time ranges and records, correct malicious entries, and communicate confirmed scope and recovery. Receipt-based deletion only removes the application record, not platform logs/backups or third-party copies.

## Residual risks and verification limits
Sites runtime logs were observed to contain IP headers. Older status requests included account URLs in the same log. This change cannot erase those logs or guarantee request-body logging will never be enabled by the provider. A full hosting-account compromise may expose data and secrets. HMAC is pseudonymization, not guaranteed anonymization. DNS preflight checks complement a fixed host allowlist but do not pin the subsequent connection against DNS changes. AI screening does not prove account ownership or prevent all prompt injection. Large distributed denial of service requires provider-level controls.

Security logic tests and production build must pass before deployment. The bundled Node HTML-render test cannot import the Cloudflare runtime module directly; this is an environment limitation, not a passing render test.
