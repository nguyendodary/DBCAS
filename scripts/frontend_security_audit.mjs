#!/usr/bin/env node
// Frontend security audit with one time-boxed, advisory-scoped exception.
//
// The exception applies only to GHSA-fc5q-39xc-vjpf (picomatch ReDoS, no
// patched release as of 2026-11-18). Every other advisory remains fatal.
// No exit-code suppression, audit-level change, or step skip is used.
//
// Test-only overrides:
//   DBCAS_SECURITY_AUDIT_NOW=YYYY-MM-DD  simulate the effective date
//   DBCAS_AUDIT_JSON_FILE=/path/audit.json  parse a supplied audit report

import fs from 'node:fs';
import { spawnSync } from 'node:child_process';

const ADVISORY_DISPLAY = 'GHSA-fc5q-39xc-vjpf';
const ADVISORY = ADVISORY_DISPLAY.toUpperCase();
const EXPIRY = process.env.DBCAS_AUDIT_EXCEPTION_EXPIRY || '2026-12-18';
const NOW =
  process.env.DBCAS_SECURITY_AUDIT_NOW || new Date().toISOString().slice(0, 10);

console.log(`frontend security audit exception: ${ADVISORY_DISPLAY}`);
console.log(`exception expiry: ${EXPIRY}`);
console.log(`effective date: ${NOW}`);

if (NOW > EXPIRY) {
  console.log('EXCEPTION EXPIRED: applying full npm audit --audit-level=high');
  const result = spawnSync(
    'npm',
    ['--prefix', 'frontend', 'audit', '--audit-level=high'],
    { stdio: 'inherit', shell: process.platform === 'win32' }
  );
  if (result.error) {
    console.error(`npm audit could not start: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.log(
  `EXCEPTION ACTIVE: only ${ADVISORY_DISPLAY} will be accepted; all other advisories fail`
);

let stdout = '';
let status = 0;
const auditFile = process.env.DBCAS_AUDIT_JSON_FILE;

if (auditFile) {
  stdout = fs.readFileSync(auditFile, 'utf8');
  status = 1;
  console.log(`test mode: using supplied audit report ${auditFile}`);
} else {
  const result = spawnSync(
    'npm',
    ['--prefix', 'frontend', 'audit', '--json', '--audit-level=high'],
    { encoding: 'utf8', shell: process.platform === 'win32' }
  );
  if (result.error) {
    console.error(`npm audit could not start: ${result.error.message}`);
    process.exit(1);
  }
  stdout = result.stdout || '';
  status = result.status ?? 1;
  if (result.stderr) process.stderr.write(result.stderr);
}

if (status === 0) {
  console.log('npm audit --audit-level=high: PASS (no high/critical advisories)');
  process.exit(0);
}

let audit;
try {
  audit = JSON.parse(stdout.replace(/^\uFEFF/, ''));
} catch (error) {
  console.error(`npm audit JSON could not be parsed: ${error.message}`);
  process.exit(1);
}

const found = new Set();
for (const vulnerability of Object.values(audit.vulnerabilities || {})) {
  for (const via of vulnerability?.via || []) {
    if (!via || typeof via !== 'object') continue;
    const match = String(via.url || '').match(/GHSA-[a-z0-9-]+/i);
    if (match) found.add(match[0].toUpperCase());
  }
}

const counts = audit.metadata?.vulnerabilities || {};
console.log(
  `npm audit summary: high=${counts.high ?? 0} critical=${counts.critical ?? 0} total=${counts.total ?? 0}`
);
console.log(`advisories found: ${[...found].join(', ') || 'none'}`);

const other = [...found].filter((id) => id !== ADVISORY);
if (other.length > 0) {
  console.error(`BLOCKED: unexpected advisories: ${other.join(', ')}`);
  process.exit(1);
}

if (found.size === 0 && ((counts.high ?? 0) + (counts.critical ?? 0)) > 0) {
  console.error('BLOCKED: high/critical advisories without recognized advisory IDs');
  process.exit(1);
}

console.log(
  `ACCEPTED: only ${ADVISORY_DISPLAY}; exception active until ${EXPIRY}; all other advisories remain fatal`
);
process.exit(0);
