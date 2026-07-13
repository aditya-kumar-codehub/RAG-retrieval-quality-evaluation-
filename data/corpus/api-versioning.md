# API Versioning

Northwind Cloud's API is versioned in the URL path, e.g. `https://api.northwindcloud.com/v2/customers`. The current stable version is `v2`. Version `v1` is deprecated but still operational.

When a new major version is released, the previous version enters a deprecation period of 6 months, during which it continues to function but returns a `Deprecation` header on every response pointing to the migration guide. After the 6-month deprecation period, the old version is sunset and requests to it return `410 Gone` after an additional 6-month grace period — meaning a deprecated version remains callable, with warnings, for a full 12 months after its successor ships.

Minor, backwards-compatible changes (new optional fields, new endpoints) are shipped continuously without a version bump. Breaking changes always require a new major version. A running log of notable changes is kept in `api-changelog.md`, including the deprecation of several `v1`-only fields that were replaced by more consistent naming in `v2`.

Client libraries (see `sdks.md`) pin to a specific API version by default and must be explicitly upgraded to opt into a new major version.
