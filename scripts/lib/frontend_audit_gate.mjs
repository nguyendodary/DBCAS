// Pure validation helpers for the frontend security audit gate.
//
// This module deliberately has no environment or process side effects so the
// fail-closed rules can be exercised with fixtures in regression tests.

export const ALLOWED_ADVISORY = 'GHSA-FC5Q-39XC-VJPF';
export const ALLOWED_ADVISORY_DISPLAY = 'GHSA-fc5q-39xc-vjpf';
export const EXPIRY_DATE = '2026-12-18';

const SEVERITIES = ['info', 'low', 'moderate', 'high', 'critical'];
const SEVERITY_SET = new Set(SEVERITIES);
const GHSA_ID = '[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}';
const ADVISORY_URL = new RegExp(
  `^https://github\\.com/advisories/(GHSA-${GHSA_ID})$`,
  'i'
);
const LEGACY_OVERRIDE_ENV = [
  'DBCAS_AUDIT_EXCEPTION_EXPIRY',
  'DBCAS_SECURITY_AUDIT_NOW',
  'DBCAS_AUDIT_JSON_FILE',
];

export class AuditValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'AuditValidationError';
  }
}

function fail(message) {
  throw new AuditValidationError(message);
}

function hasOwn(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function utcDateString(now = new Date()) {
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) {
    throw new Error('invalid current date');
  }
  return now.toISOString().slice(0, 10);
}

export function isExpired(now = new Date(), expiry = EXPIRY_DATE) {
  if (typeof expiry !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(expiry)) {
    throw new Error('invalid expiry date');
  }
  return utcDateString(now) > expiry;
}

export function getAuditPlan(now = new Date()) {
  if (isExpired(now)) {
    return {
      mode: 'full',
      args: ['--prefix', 'frontend', 'audit', '--audit-level=high'],
    };
  }
  return {
    mode: 'scoped',
    args: ['--prefix', 'frontend', 'audit', '--json', '--audit-level=high'],
  };
}

export function assertNoLegacyOverrides(env = process.env) {
  const present = LEGACY_OVERRIDE_ENV.filter((name) => hasOwn(env, name));
  if (present.length > 0) {
    throw new Error(
      `legacy audit override(s) are not allowed in normal execution: ${present.join(', ')}`
    );
  }
}

export function parseAuditJson(stdout) {
  if (typeof stdout !== 'string') {
    throw new Error('audit output is not text');
  }
  const text = stdout.replace(/^\uFEFF/, '').trim();
  if (text.length === 0) {
    throw new Error('audit output is empty');
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`audit output is not valid JSON: ${error.message}`);
  }
}

function readAdvisory(via, packageName, index) {
  if (!isPlainObject(via)) {
    fail(`unknown via[${index}] structure for "${packageName}"`);
  }
  if (typeof via.url !== 'string') {
    fail(`via[${index}] for "${packageName}" has no advisory URL`);
  }
  const match = via.url.match(ADVISORY_URL);
  if (!match) {
    fail(`via[${index}] for "${packageName}" has a non-GHSA advisory URL`);
  }
  const advisory = match[1].toUpperCase();
  if (advisory !== ALLOWED_ADVISORY) {
    fail(
      `via[${index}] for "${packageName}" references disallowed advisory ${advisory}`
    );
  }
  if (hasOwn(via, 'severity') && !SEVERITY_SET.has(via.severity)) {
    fail(
      `via[${index}] for "${packageName}" has unknown severity ${JSON.stringify(via.severity)}`
    );
  }
  return advisory;
}

function validateReport(report, npmExitStatus) {
  if (
    !Number.isInteger(npmExitStatus) ||
    (npmExitStatus !== 0 && npmExitStatus !== 1)
  ) {
    fail(
      `npm audit exit status ${JSON.stringify(npmExitStatus)} is not 0 or 1`
    );
  }
  if (!isPlainObject(report)) {
    fail('audit report is not a JSON object');
  }
  if (hasOwn(report, 'error') || hasOwn(report, 'message')) {
    fail('audit report contains an error or message field');
  }
  if (report.auditReportVersion !== 2) {
    fail(
      `unsupported auditReportVersion ${JSON.stringify(report.auditReportVersion)}`
    );
  }
  if (!isPlainObject(report.vulnerabilities)) {
    fail('audit report vulnerabilities is missing or invalid');
  }
  if (!isPlainObject(report.metadata)) {
    fail('audit report metadata is missing or invalid');
  }
  const counts = report.metadata.vulnerabilities;
  if (!isPlainObject(counts)) {
    fail('metadata.vulnerabilities is missing or invalid');
  }
  for (const severity of [...SEVERITIES, 'total']) {
    if (!Number.isInteger(counts[severity]) || counts[severity] < 0) {
      fail(`metadata.vulnerabilities.${severity} is missing or invalid`);
    }
  }
  const severitySum = SEVERITIES.reduce(
    (sum, severity) => sum + counts[severity],
    0
  );
  if (severitySum !== counts.total) {
    fail(
      `metadata.vulnerabilities.total ${counts.total} does not equal severity sum ${severitySum}`
    );
  }

  const entries = new Map();
  const packageNames = Object.keys(report.vulnerabilities);
  if (packageNames.length !== counts.total) {
    fail(
      `vulnerabilities contains ${packageNames.length} packages but metadata.total is ${counts.total}`
    );
  }

  for (const packageName of packageNames) {
    if (packageName.length === 0) {
      fail('vulnerabilities contains an empty package name');
    }
    const entry = report.vulnerabilities[packageName];
    if (!isPlainObject(entry)) {
      fail(`vulnerability entry for "${packageName}" is not an object`);
    }
    if (!SEVERITY_SET.has(entry.severity)) {
      fail(
        `vulnerability entry for "${packageName}" has unknown severity ${JSON.stringify(entry.severity)}`
      );
    }
    if (!Array.isArray(entry.via)) {
      fail(`vulnerability entry for "${packageName}" has no via array`);
    }
    if (entry.via.length === 0) {
      fail(`vulnerability entry for "${packageName}" has an empty via array`);
    }
    const advisories = [];
    const references = [];
    for (const [index, via] of entry.via.entries()) {
      if (typeof via === 'string') {
        if (via.length === 0) {
          fail(`via[${index}] for "${packageName}" is an empty package reference`);
        }
        references.push(via);
        continue;
      }
      advisories.push(readAdvisory(via, packageName, index));
    }
    entries.set(packageName, {
      name: packageName,
      severity: entry.severity,
      advisories,
      references,
    });
  }

  const actualCounts = Object.fromEntries(
    SEVERITIES.map((severity) => [severity, 0])
  );
  for (const entry of entries.values()) {
    actualCounts[entry.severity] += 1;
  }
  for (const severity of SEVERITIES) {
    if (actualCounts[severity] !== counts[severity]) {
      fail(
        `metadata.vulnerabilities.${severity} is ${counts[severity]} but vulnerabilities contains ${actualCounts[severity]}`
      );
    }
  }

  for (const entry of entries.values()) {
    for (const reference of entry.references) {
      if (!entries.has(reference)) {
        fail(
          `unresolvable package reference "${reference}" from "${entry.name}"`
        );
      }
    }
  }

  const visiting = new Set();
  const visited = new Set();
  function visit(packageName) {
    if (visited.has(packageName)) return;
    if (visiting.has(packageName)) {
      fail(`cyclic via chain at "${packageName}"`);
    }
    visiting.add(packageName);
    for (const reference of entries.get(packageName).references) {
      visit(reference);
    }
    visiting.delete(packageName);
    visited.add(packageName);
  }
  for (const packageName of entries.keys()) {
    visit(packageName);
  }

  const attributable = new Map();
  function proveAttribution(packageName) {
    if (attributable.has(packageName)) return true;
    const entry = entries.get(packageName);
    let proved = entry.advisories.length > 0;
    for (const reference of entry.references) {
      if (!proveAttribution(reference)) {
        fail(
          `"${packageName}" references "${reference}" which is not attributable to ${ALLOWED_ADVISORY_DISPLAY}`
        );
      }
      proved = true;
    }
    if (!proved) {
      fail(`"${packageName}" has no advisory attribution`);
    }
    attributable.set(packageName, true);
    return true;
  }
  for (const entry of entries.values()) {
    if (entry.severity === 'high' || entry.severity === 'critical') {
      proveAttribution(entry.name);
    }
  }

  const highCritical = counts.high + counts.critical;
  if (npmExitStatus === 0 && highCritical > 0) {
    fail('npm audit exited 0 but reported high or critical vulnerabilities');
  }
  if (npmExitStatus === 1 && highCritical === 0) {
    fail('npm audit exited 1 but reported no high or critical vulnerabilities');
  }

  return {
    npmExitStatus,
    high: counts.high,
    critical: counts.critical,
    total: counts.total,
    advisories: [
      ...new Set(
        [...entries.values()].flatMap((entry) => entry.advisories)
      ),
    ],
    packages: packageNames,
  };
}

export function validateAuditReport(report, { npmExitStatus } = {}) {
  try {
    return { ok: true, summary: validateReport(report, npmExitStatus) };
  } catch (error) {
    if (error instanceof AuditValidationError) {
      return { ok: false, reason: error.message };
    }
    throw error;
  }
}
