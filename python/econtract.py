#!/usr/bin/env python3
"""eContract REST API example: send a contract for signature, track it, download the signed PDF.

Python 3.8+, standard library only.

  export ECONTRACT_API_KEY=cl_live_...
  python econtract.py send contract.pdf "Alice <alice@example.com>" "Bob <bob@example.com>" --anchor "PARTY A" --anchor "PARTY B"
  python econtract.py status <contractId>
  python econtract.py links <contractId>
  python econtract.py download <contractId>
  python econtract.py void <contractId> "Sent by mistake"
"""
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

API = os.environ.get("ECONTRACT_API_URL", "https://api.econtract.online/api/v1")
KEY = os.environ.get("ECONTRACT_API_KEY")


def call(method, path, body=None, idempotent=False, raw=False):
    headers = {"Authorization": f"Bearer {KEY}", "User-Agent": "contractlayer-example/1.0"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if idempotent:
        # A retried request with the same key is answered once, not executed twice
        headers["Idempotency-Key"] = str(uuid.uuid4())
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            payload = res.read()
            return (payload, dict(res.headers)) if raw else json.loads(payload)
    except urllib.error.HTTPError as err:
        raise SystemExit(f"{method} {path} -> HTTP {err.code}: {err.read().decode()[:500]}")


def parse_signer(text):
    """'Alice <alice@example.com>' -> {'name': 'Alice', 'email': 'alice@example.com'}"""
    m = re.match(r"^\s*(.*?)\s*<([^>]+)>\s*$", text)
    return {"name": m.group(1) or m.group(2), "email": m.group(2)} if m else {"name": text, "email": text}


def wait_until_ready(contract_id):
    for _ in range(30):
        c = call("GET", f"/contracts/{contract_id}")
        if c["processingStatus"] == "ready":
            return c
        if c["processingStatus"] == "failed":
            raise SystemExit(f"Preparation failed: {c.get('processingError')}")
        time.sleep(2)
    raise SystemExit("Still processing after 60 s")


def send(path, args):
    anchors, signers, i = [], [], 0
    while i < len(args):
        if args[i] == "--anchor":
            anchors.append(args[i + 1])
            i += 2
        else:
            signers.append(parse_signer(args[i]))
            i += 1
    if not path or not signers:
        raise SystemExit('Usage: send <file.pdf|file.docx> "Name <email>" [...] [--anchor "TEXT"]...')

    filename = os.path.basename(path)
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    is_docx = filename.lower().endswith(".docx")
    body = {
        "title": re.sub(r"\.(pdf|docx)$", "", filename, flags=re.I),
        "signingOrderType": "sequential",
        # "link": no invitation emails, you share the links yourself. Use "email" to let eContract email them.
        "delivery": "link",
        "signers": [
            {
                "signerType": "external",
                "name": s["name"],
                "email": s["email"],
                "signOrder": n + 1,
                # The signature box goes below this text (and its caption lines) in the document
                **({"signatureAnchor": {"text": anchors[n]}} if n < len(anchors) else {}),
            }
            for n, s in enumerate(signers)
        ],
        "files": [
            {
                "filename": filename,
                "contentBase64": content,
                "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if is_docx else "application/pdf",
            }
        ],
    }
    created = call("POST", "/contracts/send", body, idempotent=True)
    print(f"Created {created['code']} ({created['id']}), preparing the document...")
    wait_until_ready(created["id"])
    links(created["id"])


def status(contract_id):
    c = call("GET", f"/contracts/{contract_id}")
    print(f'{c["code"]} "{c["title"]}": {c["status"]} (processing {c["processingStatus"]})')
    for s in c.get("signers", []):
        print(f'  {s.get("signOrder")}. {s.get("signerName") or s.get("name")} <{s.get("signerEmail") or s.get("email")}>: {s.get("status")}')


def links(contract_id):
    res = call("POST", f"/contracts/{contract_id}/signing-links", {}, idempotent=True)
    items = res["data"] if isinstance(res, dict) and "data" in res else res
    print("Signing links (give each person only their own):")
    for l in items:
        print(f'  {l.get("name") or l.get("signerName")} <{l.get("email") or l.get("signerEmail")}>: {l.get("signingUrl") or l.get("status")}')


def download(contract_id):
    pdf, headers = call("GET", f"/contracts/{contract_id}/document", raw=True)
    version = {k.lower(): v for k, v in headers.items()}.get("x-document-version", "current")
    with open(f"{contract_id}-{version}.pdf", "wb") as f:
        f.write(pdf)
    with open(f"{contract_id}-audit-trail.json", "w") as f:
        json.dump(call("GET", f"/contracts/{contract_id}/audit-trail"), f, indent=2)
    print(f"Saved {contract_id}-{version}.pdf and {contract_id}-audit-trail.json")


def void(contract_id, reason="Cancelled"):
    call("POST", f"/contracts/{contract_id}/void", {"reason": reason}, idempotent=True)
    print(f"Voided {contract_id}")


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Set ECONTRACT_API_KEY (create one at https://econtract.online/dashboard/api-keys)")
    cmd, rest = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    commands = {
        "send": lambda: send(rest[0] if rest else "", rest[1:]),
        "status": lambda: status(rest[0]),
        "links": lambda: links(rest[0]),
        "download": lambda: download(rest[0]),
        "void": lambda: void(*rest[:2]),
    }
    if cmd not in commands:
        raise SystemExit("Commands: send, status, links, download, void (see the top of this file)")
    commands[cmd]()
