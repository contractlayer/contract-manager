#!/usr/bin/env node
// eContract REST API example: send a contract for signature, track it, download the signed PDF.
// Node.js 18+ (built-in fetch), no dependencies.
//
//   export ECONTRACT_API_KEY=cl_live_...
//   node econtract.mjs send contract.pdf "Alice <alice@example.com>" "Bob <bob@example.com>" --anchor "PARTY A" --anchor "PARTY B"
//   node econtract.mjs status <contractId>
//   node econtract.mjs links <contractId>
//   node econtract.mjs download <contractId>
//   node econtract.mjs void <contractId> "Sent by mistake"

import { randomUUID } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { basename } from 'node:path';

const API = process.env.ECONTRACT_API_URL || 'https://api.econtract.online/api/v1';
const KEY = process.env.ECONTRACT_API_KEY;
if (!KEY) {
  console.error('Set ECONTRACT_API_KEY (create one at https://econtract.online/dashboard/api-keys)');
  process.exit(1);
}

async function call(method, path, { body, idempotent = false, raw = false } = {}) {
  const headers = { Authorization: `Bearer ${KEY}` };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  // Writes carry an Idempotency-Key: a retried request is answered once, not executed twice
  if (idempotent) headers['Idempotency-Key'] = randomUUID();
  const res = await fetch(`${API}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${method} ${path} → HTTP ${res.status}: ${text.slice(0, 500)}`);
  }
  return raw ? res : res.json();
}

/** "Alice <alice@example.com>" → { name, email } */
function parseSigner(text) {
  const m = text.match(/^\s*(.*?)\s*<([^>]+)>\s*$/);
  return m ? { name: m[1] || m[2], email: m[2] } : { name: text, email: text };
}

async function waitUntilReady(id) {
  for (let i = 0; i < 30; i++) {
    const c = await call('GET', `/contracts/${id}`);
    if (c.processingStatus === 'ready') return c;
    if (c.processingStatus === 'failed') throw new Error(`Preparation failed: ${c.processingError}`);
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error('Still processing after 60 s');
}

async function send(file, args) {
  const anchors = [];
  const signers = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--anchor') anchors.push(args[++i]);
    else signers.push(parseSigner(args[i]));
  }
  if (!file || signers.length === 0) throw new Error('Usage: send <file.pdf|file.docx> "Name <email>" [...] [--anchor "TEXT"]...');

  const body = {
    title: basename(file).replace(/\.(pdf|docx)$/i, ''),
    signingOrderType: 'sequential',
    // "link": no invitation emails, you share the links yourself. Use "email" to let eContract email them.
    delivery: 'link',
    signers: signers.map((s, i) => ({
      signerType: 'external',
      name: s.name,
      email: s.email,
      signOrder: i + 1,
      // The signature box goes below this text (and its caption lines) in the document
      ...(anchors[i] && { signatureAnchor: { text: anchors[i] } }),
    })),
    files: [
      {
        filename: basename(file),
        contentBase64: readFileSync(file).toString('base64'),
        contentType: file.toLowerCase().endsWith('.docx')
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf',
      },
    ],
  };

  const created = await call('POST', '/contracts/send', { body, idempotent: true });
  console.log(`Created ${created.code} (${created.id}), preparing the document...`);
  await waitUntilReady(created.id);
  await links(created.id);
}

async function status(id) {
  const c = await call('GET', `/contracts/${id}`);
  console.log(`${c.code} "${c.title}": ${c.status} (processing ${c.processingStatus})`);
  for (const s of c.signers ?? []) console.log(`  ${s.signOrder}. ${s.signerName ?? s.name} <${s.signerEmail ?? s.email}>: ${s.status}`);
}

async function links(id) {
  const res = await call('POST', `/contracts/${id}/signing-links`, { body: {}, idempotent: true });
  const items = Array.isArray(res.data) ? res.data : res;
  console.log('Signing links (give each person only their own):');
  for (const l of items) console.log(`  ${l.name ?? l.signerName} <${l.email ?? l.signerEmail}>: ${l.signingUrl ?? l.status}`);
}

async function download(id) {
  const res = await call('GET', `/contracts/${id}/document`, { raw: true });
  const version = res.headers.get('x-document-version') || 'current';
  const pdf = `${id}-${version}.pdf`;
  writeFileSync(pdf, Buffer.from(await res.arrayBuffer()));
  const audit = await call('GET', `/contracts/${id}/audit-trail`);
  writeFileSync(`${id}-audit-trail.json`, JSON.stringify(audit, null, 2));
  console.log(`Saved ${pdf} and ${id}-audit-trail.json`);
}

async function voidContract(id, reason = 'Cancelled') {
  await call('POST', `/contracts/${id}/void`, { body: { reason }, idempotent: true });
  console.log(`Voided ${id}`);
}

const [command, ...rest] = process.argv.slice(2);
const commands = { send: () => send(rest[0], rest.slice(1)), status: () => status(rest[0]), links: () => links(rest[0]), download: () => download(rest[0]), void: () => voidContract(rest[0], rest[1]) };
if (!commands[command]) {
  console.error('Commands: send, status, links, download, void (see the top of this file)');
  process.exit(1);
}
commands[command]().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
