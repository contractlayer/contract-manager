# contract-manager

Send a contract for e-signature with the [eContract](https://econtract.online) REST API, place the signatures automatically, share the signing links and download the signed PDF with its audit trail.

Two small command-line examples, same commands:

- [`node/econtract.mjs`](node/econtract.mjs): Node.js 18+, no dependencies
- [`python/econtract.py`](python/econtract.py): Python 3.8+, standard library only

## Run it

1. Create a free account at [econtract.online](https://econtract.online) and an API key under **Dashboard → API keys**.
2. Send the sample agreement to two people (signing links only, no emails are sent):

```bash
export ECONTRACT_API_KEY=cl_live_...
node node/econtract.mjs send samples/service-agreement.pdf \
  "Alice <alice@example.com>" "Bob <bob@example.com>" \
  --anchor "PARTY A" --anchor "PARTY B"
```

```text
Created CTR-20261017-UM3RC6 (a42731f2-…), preparing the document...
Signing links (give each person only their own):
  Alice <alice@example.com>: https://econtract.online/sign/0a64c4…
  Bob <bob@example.com>: https://econtract.online/sign/b0c01b…
```

Use `python3 python/econtract.py …` for the Python version.

## Commands

| Command | API calls |
|---|---|
| `send <file.pdf\|file.docx> "Name <email>"… [--anchor TEXT]…` | `POST /contracts/send`, then `GET /contracts/{id}` until `processingStatus` is `ready`, then `POST /contracts/{id}/signing-links` |
| `status <id>` | `GET /contracts/{id}` |
| `links <id>` | `POST /contracts/{id}/signing-links` (fresh links, no email) |
| `download <id>` | `GET /contracts/{id}/document` (the signed PDF once everyone has signed) and `GET /contracts/{id}/audit-trail` |
| `void <id> [reason]` | `POST /contracts/{id}/void` |

All calls go to `https://api.econtract.online/api/v1` with `Authorization: Bearer <key>`.

## What the example shows

- **Signature placement by anchor text.** Each `--anchor` is a text printed where that signer signs (here `PARTY A`, `PARTY B`). eContract finds it in the PDF and puts the signature box below it and below caption lines such as "(Signature, full name)". No coordinates needed. Without an anchor, signers get their own box at the bottom of the last page.
- **Signing order.** Signers sign in the order given (`signingOrderType: "sequential"`); use `"parallel"` to let everyone sign at once.
- **Delivery.** `delivery: "link"` sends no email: you share each person's own link. `"email"` lets eContract email the invitations, `"both"` does both.
- **Idempotency.** Every write carries an `Idempotency-Key`, so a retried request is answered once instead of creating a second contract.
- **Signing stays with people.** API keys and agents can prepare and send, never sign or decline for someone.

## Use it from an AI agent instead

The same operations are tools on the eContract MCP server (`https://api.econtract.online/mcp`): `send_contract`, `get_contract`, `get_signing_links`, `download_signed_document`, `get_audit_trail`, `void_contract`. Client setup: [contractlayer/contractlayer → mcp](https://github.com/contractlayer/contractlayer/tree/main/mcp).

## Links

- [API reference](https://developers.econtract.online/docs) and [OpenAPI document](https://api.econtract.online/api/v1/openapi.json)
- [Signature placement](https://developers.econtract.online/docs/mcp#signature-placement)
- [Verify a signed PDF](https://github.com/contractlayer/verify-pdf)

## License

MIT
