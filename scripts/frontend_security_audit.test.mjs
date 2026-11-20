import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  assertNoLegacyOverrides,
  parseAuditJson,
  validateAuditReport,
} from './lib/frontend_audit_gate.mjs';

const FORMER_EXCEPTION_URL = 'https://github.com/advisories/GHSA-fc5q-39xc-vjpf';
const DIFFERENT_GHSA_URL =
  'https://github.com/advisories/GHSA-aaaa-bbbb-cccc';
const NON_GHSA_URL = 'https://example.invalid/CVE-2026-99999';

function advisory(url = FORMER_EXCEPTION_URL, severity = 'high') {
  return {
    source: 1,
    name: 'picomatch',
    dependency: 'picomatch',
    title: 'picomatch vulnerable to ReDoS',
    url,
    severity,
    cwe: ['CWE-1333'],
    cvss: { score: 7.5 },
    range: '<=4.0.7',
  };
}

function entry(severity, via, name = 'picomatch') {
  return {
    name,
    severity,
    isDirect: false,
    via,
    effects: [],
    range: '<=4.0.7',
    nodes: [`node_modules/${name}`],
    fixAvailable: true,
  };
}

function counts(overrides = {}) {
  return {
    info: 0,
    low: 0,
    moderate: 0,
    high: 0,
    critical: 0,
    total: 0,
    ...overrides,
  };
}

function baselineReport() {
  return {
    auditReportVersion: 2,
    vulnerabilities: {
      picomatch: entry('high', [advisory()]),
      fdir: entry('high', ['picomatch'], 'fdir'),
      tinyglobby: entry('high', ['fdir', 'picomatch'], 'tinyglobby'),
      vite: entry('high', ['picomatch', 'tinyglobby'], 'vite'),
      vitest: entry('high', ['picomatch', 'tinyglobby'], 'vitest'),
      '@vitejs/plugin-react': entry('high', ['vite'], '@vitejs/plugin-react'),
    },
    metadata: {
      vulnerabilities: counts({ high: 6, total: 6 }),
    },
  };
}

function singleReport({ severity = 'high', via = [advisory()] } = {}) {
  return {
    auditReportVersion: 2,
    vulnerabilities: {
      picomatch: entry(severity, via),
    },
    metadata: {
      vulnerabilities: counts({
        moderate: severity === 'moderate' ? 1 : 0,
        high: severity === 'high' ? 1 : 0,
        critical: severity === 'critical' ? 1 : 0,
        total: 1,
      }),
    },
  };
}

function noVulnerabilityReport() {
  return {
    auditReportVersion: 2,
    vulnerabilities: {},
    metadata: { vulnerabilities: counts() },
  };
}

test('formerly excepted picomatch advisory -> FAIL', () => {
  const result = validateAuditReport(baselineReport(), { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /high or critical vulnerabilities/);
});

test('different GHSA high -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({ via: [advisory(DIFFERENT_GHSA_URL)] }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /high or critical vulnerabilities/);
});

test('different GHSA critical -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({
      severity: 'critical',
      via: [advisory(DIFFERENT_GHSA_URL, 'critical')],
    }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /high or critical vulnerabilities/);
});

test('non-GHSA high -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({ via: [advisory(NON_GHSA_URL)] }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /non-GHSA advisory URL/);
});

test('non-GHSA critical -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({
      severity: 'critical',
      via: [advisory(NON_GHSA_URL, 'critical')],
    }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /non-GHSA advisory URL/);
});

test('mixed GHSA findings -> FAIL', () => {
  const report = baselineReport();
  report.vulnerabilities.otherpkg = entry(
    'high',
    [advisory(DIFFERENT_GHSA_URL)],
    'otherpkg'
  );
  report.metadata.vulnerabilities = counts({ high: 7, total: 7 });
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /high or critical vulnerabilities/);
});

test('empty JSON -> FAIL', () => {
  const result = validateAuditReport({}, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /auditReportVersion/);
});

test('missing metadata -> FAIL', () => {
  const report = baselineReport();
  delete report.metadata;
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /metadata is missing or invalid/);
});

test('missing vulnerabilities -> FAIL', () => {
  const report = baselineReport();
  delete report.vulnerabilities;
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /vulnerabilities is missing or invalid/);
});

test('registry error -> FAIL', () => {
  const result = validateAuditReport(
    {
      message:
        'request to https://registry.npmjs.org/-/npm/v1/security/advisories/bulk failed',
      error: { summary: '', detail: '' },
    },
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /error or message field/);
});

test('malformed JSON -> FAIL', () => {
  assert.throws(
    () => parseAuditJson('{"auditReportVersion": 2'),
    /not valid JSON/
  );
  assert.throws(() => parseAuditJson(''), /audit output is empty/);
});

test('unknown via chain -> FAIL', () => {
  const unknown = validateAuditReport(singleReport({ via: [42] }), {
    npmExitStatus: 1,
  });
  assert.equal(unknown.ok, false);
  assert.match(unknown.reason, /unknown via\[0\] structure/);

  const missingUrl = validateAuditReport(
    singleReport({ via: [{ severity: 'high' }] }),
    { npmExitStatus: 1 }
  );
  assert.equal(missingUrl.ok, false);
  assert.match(missingUrl.reason, /has no advisory URL/);
});

test('unresolvable package reference -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({ via: ['missing-package'] }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(
    result.reason,
    /unresolvable package reference "missing-package"/
  );
});

test('test-mode bypass attempt in GitHub Actions -> FAIL', () => {
  for (const name of [
    'DBCAS_AUDIT_EXCEPTION_EXPIRY',
    'DBCAS_SECURITY_AUDIT_NOW',
    'DBCAS_AUDIT_JSON_FILE',
  ]) {
    assert.throws(
      () => assertNoLegacyOverrides({ GITHUB_ACTIONS: 'true', [name]: 'x' }),
      /legacy audit override/
    );
  }
  assert.doesNotThrow(() =>
    assertNoLegacyOverrides({ GITHUB_ACTIONS: 'true' })
  );
});

test('npm exit 0 with high findings -> FAIL', () => {
  const result = validateAuditReport(singleReport(), { npmExitStatus: 0 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /exited 0 but reported high or critical/);
});

test('npm exit 1 with no high or critical findings -> FAIL', () => {
  const result = validateAuditReport(noVulnerabilityReport(), {
    npmExitStatus: 1,
  });
  assert.equal(result.ok, false);
  assert.match(result.reason, /exited 1 but reported no high or critical/);
});

test('moderate finding stays below the high threshold', () => {
  const result = validateAuditReport(
    singleReport({ severity: 'moderate', via: [advisory(DIFFERENT_GHSA_URL, 'moderate')] }),
    { npmExitStatus: 0 }
  );
  assert.equal(result.ok, true);
  assert.equal(result.summary.total, 1);
});

test('clean report with npm exit 0 -> PASS', () => {
  const result = validateAuditReport(noVulnerabilityReport(), {
    npmExitStatus: 0,
  });
  assert.equal(result.ok, true);
  assert.equal(result.summary.high, 0);
  assert.equal(result.summary.critical, 0);
  assert.deepEqual(result.summary.advisories, []);
});

test('metadata package counts must match vulnerability entries', () => {
  const report = baselineReport();
  report.metadata.vulnerabilities = counts({ high: 5, total: 5 });
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(
    result.reason,
    /vulnerabilities contains 6 packages but metadata.total is 5/
  );
});

test('cyclic via chain -> FAIL', () => {
  const report = baselineReport();
  report.vulnerabilities.fdir.via = ['picomatch', 'vite'];
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /cyclic via chain/);
});

test('unknown auditReportVersion -> FAIL', () => {
  const report = baselineReport();
  report.auditReportVersion = 3;
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /unsupported auditReportVersion/);
});

test('non-object vulnerabilities or metadata counts -> FAIL', () => {
  const arrayReport = baselineReport();
  arrayReport.vulnerabilities = [];
  assert.match(
    validateAuditReport(arrayReport, { npmExitStatus: 1 }).reason,
    /vulnerabilities is missing or invalid/
  );

  const stringCounts = baselineReport();
  stringCounts.metadata.vulnerabilities.high = '6';
  assert.match(
    validateAuditReport(stringCounts, { npmExitStatus: 1 }).reason,
    /metadata\.vulnerabilities\.high is missing or invalid/
  );
});

test('non-GitHub URL carrying the former exception id -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({
      via: [
        advisory(
          'https://example.invalid/advisories/GHSA-fc5q-39xc-vjpf'
        ),
      ],
    }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /non-GHSA advisory URL/);
});

test('valid JSON with UTF-8 BOM -> PASS', () => {
  const parsed = parseAuditJson(`\uFEFF${JSON.stringify(noVulnerabilityReport())}`);
  const result = validateAuditReport(parsed, { npmExitStatus: 0 });
  assert.equal(result.ok, true);
});

// ---------------------------------------------------------------------------
// npm stderr fail-closed regression tests (gap in the wrapper merged in #34).
//
// evaluateNpmAuditResult is the pure decision function the wrapper delegates
// to. Testing it here covers the exact combination reported by the mock:
// clean audit JSON + npm exit 0 + registry error on stderr.
// ---------------------------------------------------------------------------

async function loadEvaluateNpmAuditResult() {
  const gate = await import('./lib/frontend_audit_gate.mjs');
  assert.equal(
    typeof gate.evaluateNpmAuditResult,
    'function',
    'evaluateNpmAuditResult must be exported by the audit gate'
  );
  return gate.evaluateNpmAuditResult;
}

test('mock: clean JSON + exit 0 + registry error on stderr -> BLOCKED', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  const stdout = JSON.stringify(noVulnerabilityReport());

  assert.equal(evaluate({ stdout, stderr: '', status: 0 }).ok, true);

  const outcome = evaluate({
    stdout,
    stderr:
      'npm error code ECONNREFUSED\n' +
      'npm error request to https://registry.npmjs.org/-/npm/v1/security/advisories/bulk failed\n',
    status: 0,
  });
  assert.equal(outcome.ok, false, 'registry error on stderr must fail closed');
  assert.match(outcome.reason, /BLOCKED:/);
  assert.match(outcome.reason, /ECONNREFUSED/);
});

test('registry/network/audit-endpoint stderr signatures -> BLOCKED', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  const stdout = JSON.stringify(baselineReport());
  const cases = [
    ['ECONNREFUSED', 'npm error code ECONNREFUSED'],
    ['ENOTFOUND', 'npm error code ENOTFOUND'],
    ['ETIMEDOUT', 'npm error code ETIMEDOUT'],
    ['ECONNRESET', 'npm error code ECONNRESET'],
    ['EAI_AGAIN', 'npm error getaddrinfo EAI_AGAIN registry.npmjs.org'],
    [
      'audit endpoint returned an error',
      'npm error audit endpoint returned an error',
    ],
    ['HTTP 4xx', 'npm error 404 Not Found'],
    ['HTTP 5xx', 'npm error 503 Service Unavailable'],
  ];
  for (const [label, stderr] of cases) {
    const outcome = evaluate({ stdout, stderr, status: 1 });
    assert.equal(outcome.ok, false, `${label} on stderr must block`);
    assert.match(outcome.reason, /BLOCKED:/, `${label} must give a BLOCKED reason`);
  }
});

test('error signature inside an npm WARN line -> BLOCKED', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  const outcome = evaluate({
    stdout: JSON.stringify(baselineReport()),
    stderr: 'npm WARN registry audit endpoint returned an error (ECONNRESET)',
    status: 1,
  });
  assert.equal(outcome.ok, false);
  assert.match(outcome.reason, /ECONNRESET|audit-endpoint error/);
});

test('stderr failure overrides valid JSON and any exit code', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  for (const status of [0, 1]) {
    const outcome = evaluate({
      stdout: JSON.stringify(noVulnerabilityReport()),
      stderr: 'npm error code ETIMEDOUT',
      status,
    });
    assert.equal(
      outcome.ok,
      false,
      `registry stderr must block even with exit ${status}`
    );
  }
});

test('benign stderr (empty or npm WARN lines) -> PASS', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  const stdout = JSON.stringify(noVulnerabilityReport());
  const benign = [
    '',
    '   \n',
    'npm WARN deprecated foo@1.0.0: use bar instead\n',
    'npm WARN EBADENGINE Unsupported engine\n' +
      "npm WARN EBADENGINE   package: 'foo@1.0.0'\n",
    '  npm WARN old lockfile\n',
  ];
  for (const stderr of benign) {
    const outcome = evaluate({ stdout, stderr, status: 0 });
    assert.equal(
      outcome.ok,
      true,
      `benign stderr ${JSON.stringify(stderr)} must be accepted`
    );
  }
});

test('unknown stderr -> BLOCKED (allowlist)', async () => {
  const evaluate = await loadEvaluateNpmAuditResult();
  const stdout = JSON.stringify(baselineReport());
  for (const stderr of [
    'something unexpected happened\n',
    'npm ERR! code E500\n',
    'registry unavailable\n',
  ]) {
    const outcome = evaluate({ stdout, stderr, status: 1 });
    assert.equal(
      outcome.ok,
      false,
      `unknown stderr ${JSON.stringify(stderr)} must block`
    );
  }
});

test('wrapper process fails closed on mocked registry stderr', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dbcas-audit-npm-'));
  try {
    fs.writeFileSync(
      path.join(tmp, 'stdout.txt'),
      JSON.stringify(baselineReport())
    );
    fs.writeFileSync(
      path.join(tmp, 'stderr.txt'),
      'npm error code ECONNREFUSED\n'
    );
    fs.writeFileSync(path.join(tmp, 'exit.txt'), '1\n');
    fs.writeFileSync(
      path.join(tmp, 'npm-shim.cjs'),
      [
        "const fs = require('node:fs');",
        "const path = require('node:path');",
        "const dir = __dirname;",
        "process.stdout.write(fs.readFileSync(path.join(dir, 'stdout.txt'), 'utf8'));",
        "process.stderr.write(fs.readFileSync(path.join(dir, 'stderr.txt'), 'utf8'));",
        "process.exit(Number(fs.readFileSync(path.join(dir, 'exit.txt'), 'utf8').trim()));",
      ].join('\n')
    );
    if (process.platform === 'win32') {
      const cmd = '@echo off\r\nnode "%~dp0npm-shim.cjs"\r\n';
      fs.writeFileSync(path.join(tmp, 'npm.cmd'), cmd);
      fs.writeFileSync(path.join(tmp, 'npm.bat'), cmd);
    } else {
      const shim = path.join(tmp, 'npm');
      fs.writeFileSync(shim, "#!/usr/bin/env node\nrequire('./npm-shim.cjs');\n");
      fs.chmodSync(shim, 0o755);
    }

    const pathKey =
      Object.keys(process.env).find((key) => key.toUpperCase() === 'PATH') ||
      'PATH';
    const env = { ...process.env };
    for (const name of [
      'DBCAS_AUDIT_EXCEPTION_EXPIRY',
      'DBCAS_SECURITY_AUDIT_NOW',
      'DBCAS_AUDIT_JSON_FILE',
    ]) {
      delete env[name];
    }
    env[pathKey] = `${tmp}${path.delimiter}${env[pathKey] || ''}`;

    const repoRoot = path.resolve(
      path.dirname(fileURLToPath(import.meta.url)),
      '..'
    );
    const result = spawnSync(
      process.execPath,
      ['scripts/frontend_security_audit.mjs'],
      { cwd: repoRoot, env, encoding: 'utf8' }
    );
    const combined = `${result.stdout || ''}${result.stderr || ''}`;
    assert.equal(
      result.status,
      1,
      `wrapper must block; stdout=${result.stdout} stderr=${result.stderr}`
    );
    assert.match(combined, /ECONNREFUSED/);
    assert.match(combined, /BLOCKED/);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
