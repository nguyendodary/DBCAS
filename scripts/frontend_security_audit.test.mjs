import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ALLOWED_ADVISORY,
  ALLOWED_ADVISORY_DISPLAY,
  assertNoLegacyOverrides,
  getAuditPlan,
  isExpired,
  parseAuditJson,
  validateAuditReport,
} from './lib/frontend_audit_gate.mjs';

const ALLOWED_URL = `https://github.com/advisories/${ALLOWED_ADVISORY_DISPLAY}`;
const DIFFERENT_GHSA_URL =
  'https://github.com/advisories/GHSA-aaaa-bbbb-cccc';
const NON_GHSA_URL = 'https://example.invalid/CVE-2026-99999';

function advisory(url = ALLOWED_URL, severity = 'high') {
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

test('allowed advisory only -> PASS before expiry', () => {
  const result = validateAuditReport(baselineReport(), { npmExitStatus: 1 });
  assert.equal(result.ok, true);
  assert.equal(result.summary.high, 6);
  assert.equal(result.summary.critical, 0);
  assert.equal(result.summary.total, 6);
  assert.deepEqual(result.summary.advisories, [ALLOWED_ADVISORY]);
  assert.equal(isExpired(new Date('2026-12-18T23:59:59Z')), false);
});

test('different GHSA high -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({ via: [advisory(DIFFERENT_GHSA_URL)] }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /disallowed advisory GHSA-AAAA-BBBB-CCCC/);
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
  assert.match(result.reason, /disallowed advisory GHSA-AAAA-BBBB-CCCC/);
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

test('allowed + disallowed advisory -> FAIL', () => {
  const report = baselineReport();
  report.vulnerabilities.otherpkg = entry(
    'high',
    [advisory(DIFFERENT_GHSA_URL)],
    'otherpkg'
  );
  report.metadata.vulnerabilities = counts({ high: 7, total: 7 });
  const result = validateAuditReport(report, { npmExitStatus: 1 });
  assert.equal(result.ok, false);
  assert.match(result.reason, /disallowed advisory GHSA-AAAA-BBBB-CCCC/);
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

test('exactly at expiry boundary -> active', () => {
  assert.equal(isExpired(new Date('2026-12-18T00:00:00Z')), false);
  assert.equal(isExpired(new Date('2026-12-18T23:59:59Z')), false);
  assert.deepEqual(getAuditPlan(new Date('2026-12-18T23:59:59Z')), {
    mode: 'scoped',
    args: [
      '--prefix',
      'frontend',
      'audit',
      '--json',
      '--audit-level=high',
    ],
  });
});

test('after expiry -> full audit enforced', () => {
  assert.equal(isExpired(new Date('2026-12-19T00:00:00Z')), true);
  assert.deepEqual(getAuditPlan(new Date('2026-12-19T00:00:00Z')), {
    mode: 'full',
    args: ['--prefix', 'frontend', 'audit', '--audit-level=high'],
  });
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

test('non-GitHub URL carrying the allowed GHSA id -> FAIL', () => {
  const result = validateAuditReport(
    singleReport({
      via: [
        advisory(
          `https://example.invalid/advisories/${ALLOWED_ADVISORY_DISPLAY}`
        ),
      ],
    }),
    { npmExitStatus: 1 }
  );
  assert.equal(result.ok, false);
  assert.match(result.reason, /non-GHSA advisory URL/);
});

test('valid JSON with UTF-8 BOM -> PASS', () => {
  const parsed = parseAuditJson(`\uFEFF${JSON.stringify(baselineReport())}`);
  const result = validateAuditReport(parsed, { npmExitStatus: 1 });
  assert.equal(result.ok, true);
});
