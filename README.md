<p align="center">
  <img src="https://img.shields.io/badge/Status-Coming%20Soon-blue?style=flat-square" alt="Coming Soon">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

# ✍️ contract-manager

**Create, manage, and sign contracts online.** Tamper-proof digital signatures with full audit trail.

> 🚧 **Under active development** — Star this repo to get notified when we launch.

---

## What's Coming

- 📄 **Contract creation** — Upload PDF/DOCX, define signing workflow
- ✍️ **Digital signatures** — PAdES-compliant, legally binding e-signatures
- 👥 **Multi-party signing** — Sequential or parallel signing orders
- 🔐 **Tamper-proof** — Every signature cryptographically sealed with certificate chain
- 📱 **External signers** — Invite anyone to sign via email link (no account needed)
- 📋 **Audit trail** — Complete evidence package with timestamps and activity log
- 🔔 **Notifications** — Email notifications at every step
- 🏢 **Multi-tenant** — Built for SaaS from day one

## API Preview

```bash
# Create a contract
curl -X POST https://api.econtract.online/api/v1/contracts \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@contract.pdf" \
  -F "title=Service Agreement"

# Add signers
curl -X POST https://api.econtract.online/api/v1/contracts/{id}/signers \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"email": "john@acme.com", "name": "John Doe", "order": 1}'

# Send for signing
curl -X POST https://api.econtract.online/api/v1/contracts/{id}/send \
  -H "Authorization: Bearer $TOKEN"
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│  Kong API GW │────▶│ Tenant Plane│
│  (Next.js)   │     │  (Auth/Rate) │     │  (NestJS)   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌────────────┬────────────┬───┘
                    ▼            ▼            ▼
              ┌──────────┐ ┌─────────┐ ┌──────────┐
              │  MySQL    │ │  MinIO  │ │  Redis   │
              │(per-tenant│ │ (files) │ │ (cache)  │
              └──────────┘ └─────────┘ └──────────┘
```

## Related Projects

| Project | Description | Status |
|---------|-------------|--------|
| [verify-pdf](https://github.com/contractlayer/verify-pdf) | Verify digital signatures in any PDF | ✅ Live |
| [risk-check](https://github.com/contractlayer/risk-check) | AI-powered contract risk analysis | 🔜 Coming Soon |
| [contractlayer](https://github.com/contractlayer/contractlayer) | Organization overview | ✅ |

---

## 📄 License

[MIT](LICENSE)

---

<p align="center">
  <b>Built by <a href="https://econtract.online">eContract</a></b><br>
  Tamper-proof digital signatures for the modern web.
</p>
