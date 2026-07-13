# Official SDKs

Northwind Cloud maintains official client libraries for four languages:

- **Python** (`northwind-python`) — supports Python 3.9+, published on PyPI.
- **Node.js** (`@northwindcloud/node`) — supports Node 18+, published on npm.
- **Go** (`github.com/northwindcloud/go-sdk`) — supports Go 1.21+.
- **Ruby** (`northwind-ruby`) — supports Ruby 3.0+, published as a gem.

There is no official SDK for iOS, Android, Java, or any other language at this time. A community-maintained Java wrapper exists on GitHub but is not supported or endorsed by Northwind Cloud, and Northwind Cloud makes no guarantees about its correctness or upkeep.

Every official SDK pins to a specific API version (see `api-versioning.md`) at release time and handles authentication, retry-with-backoff on `429` responses (see `rate-limits.md`), and typed error exceptions (see `error-codes.md`) out of the box. SDK release notes are published alongside the general `api-changelog.md`.
