# SSO / SAML

Single sign-on via SAML 2.0 is available exclusively on the Enterprise tier (see `pricing-tiers.md`). It is not available on Free, Starter, or Pro.

SSO authenticates human users into the Northwind Cloud dashboard — it is a separate mechanism from API authentication, which always uses API keys or OAuth as described in `authentication.md`. Configuring SSO does not change how your application authenticates to the API.

To configure SSO, an account administrator provides Northwind Cloud with their identity provider's metadata URL (supported IdPs include Okta, Azure AD, and Google Workspace). Northwind Cloud auto-provisions user accounts on first SSO login using just-in-time provisioning, and de-provisions them automatically when the IdP reports the user as removed, typically within 15 minutes.

Enabling SSO automatically enables audit logging (see `audit-logs.md`) for the account, since SSO-managed accounts are expected to have a full record of authentication events for compliance purposes. This is not optional — audit logs cannot be disabled while SSO is active.
