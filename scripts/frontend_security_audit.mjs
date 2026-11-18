#!/usr/bin/env node
// Frontend security audit with one time-boxed, advisory-scoped exception.
//
// The exception applies only to GHSA-fc5q-39xc-vjpf (picomatch ReDoS).
// The validator fails closed on registry errors, malformed or incomplete
// reports, unknown via shapes, non-GHSA advisories, and any other GHSA.
// Normal execution always runs the real npm audit; there are no fixture or
// date override environment variables.

import { spawnSync } from 'node:child_process';
import {
  ALLOWED_ADVISORY_DISPLAY,
  EXPIRY_DATE,
  assertNoLegacyOverrides,
  evaluateNpmAuditResult,
  getAuditPlan,
  utcDateString,
} from './lib/frontend_audit_gate.mjs';

function runNpm(args, options = {}) {
  const result = spawnSync('npm', args, {
    shell: process.platform === 'win32',
    ...options,
  });
  if (result.error) {
    throw new Error(`npm audit could not start: ${result.error.message}`);
  }
  return result;
}

function main() {
  const now = new Date();
  console.log(`frontend security audit exception: ${ALLOWED_ADVISORY_DISPLAY}`);
  console.log(`exception expiry: ${EXPIRY_DATE}`);
  console.log(`effective date: ${utcDateString(now)}`);

  try {
    assertNoLegacyOverrides(process.env);
  } catch (error) {
    console.error(`BLOCKED: ${error.message}`);
    return 1;
  }

  const plan = getAuditPlan(now);
  if (plan.mode === 'full') {
    console.log('EXCEPTION EXPIRED: applying full npm audit --audit-level=high');
    try {
      const result = runNpm(plan.args, { stdio: 'inherit' });
      return result.status ?? 1;
    } catch (error) {
      console.error(`BLOCKED: ${error.message}`);
      return 1;
    }
  }

  console.log(
    `EXCEPTION ACTIVE: only ${ALLOWED_ADVISORY_DISPLAY} will be accepted; all other advisories fail`
  );

  let auditResult;
  try {
    auditResult = runNpm(plan.args, { encoding: 'utf8' });
  } catch (error) {
    console.error(`BLOCKED: ${error.message}`);
    return 1;
  }
  if (auditResult.stderr) {
    process.stderr.write(auditResult.stderr);
  }

  const outcome = evaluateNpmAuditResult(auditResult);
  if (!outcome.ok) {
    console.error(outcome.reason);
    return 1;
  }

  const summary = outcome.summary;
  console.log(
    `npm audit summary: high=${summary.high} critical=${summary.critical} total=${summary.total}`
  );
  console.log(
    `advisories found: ${summary.advisories.join(', ') || 'none'}`
  );

  if (summary.high + summary.critical === 0) {
    console.log(
      'npm audit --audit-level=high: PASS (no high/critical advisories)'
    );
  } else {
    console.log(
      `ACCEPTED: only ${ALLOWED_ADVISORY_DISPLAY}; exception active until ${EXPIRY_DATE}; all other advisories remain fatal`
    );
  }

  return 0;
}

process.exit(main());
