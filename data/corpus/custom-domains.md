# Custom Domains

Custom domains let you serve Northwind Cloud-hosted content (such as customer-facing invoice pages) from your own domain instead of the default `*.northwindcloud.com` subdomain. Custom domains are available on the Pro and Enterprise tiers only (see `pricing-tiers.md`); they are not available on Free or Starter.

To set up a custom domain, add a CNAME record pointing your subdomain (e.g. `billing.yourcompany.com`) to `custom.northwindcloud.com`. Once the CNAME is detected, Northwind Cloud automatically provisions a TLS certificate via Let's Encrypt, which typically completes within 15 minutes. Certificates are auto-renewed and require no maintenance on your part.

Each account can configure up to 3 custom domains on the Pro tier and an unlimited number on the Enterprise tier. Removing a custom domain immediately reverts traffic to the default `*.northwindcloud.com` subdomain for that resource; there is no downtime during removal, but there will be a TLS certificate mismatch warning for any clients that cached the custom domain's certificate.
