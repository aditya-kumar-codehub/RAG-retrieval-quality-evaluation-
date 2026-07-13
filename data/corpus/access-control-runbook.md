# Access Control Runbook

Access to internal systems follows the principle of least privilege: employees are granted only the access required for their current role, requested through an IT ticket that requires manager approval. This is the enforcement mechanism referenced generally in `security-policy.md`.

Access grants are reviewed quarterly by IT in coordination with each department head, who must re-certify that every team member's current access is still necessary; access not re-certified within the review window is automatically revoked pending manager follow-up. This quarterly cadence mirrors the disaster recovery drill cadence described in `disaster-recovery.md`, though the two processes are independent.

Standing production access for individual engineers is intentionally minimal; most production troubleshooting is done through the break-glass procedure described in `secrets-management.md`, which is fully logged and time-limited to 8 hours per grant.

Upon an employee's offboarding, all access is revoked within 24 hours of their last day, coordinated jointly by IT and the employee's manager. This includes SSO-managed access (see `sso-saml.md`), Vault access, and physical badge access. Offboarding access revocation is itself a logged event and is reviewed as part of the standard audit process.
