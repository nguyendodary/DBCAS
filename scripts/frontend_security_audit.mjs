#!/usr/bin/env node
// Reject high/critical findings and unusable audit reports.

import { spawnSync } from 'node:child_process';
import {
  assertNoLegacyOverrides,
  evaluateNpmAuditResult,
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
  try {
    assertNoLegacyOverrides(process.env);
  } catch (error) {
    console.error(`BLOCKED: ${error.message}`);
    return 1;
  }

  let auditResult;
  try {
    auditResult = runNpm(
      ['--prefix', 'frontend', 'audit', '--json', '--audit-level=high'],
      { encoding: 'utf8' }
    );
  } catch (error) {
    console.error(`BLOCKED: ${error.message}`);
    return 1;
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

  console.log('npm audit --audit-level=high: PASS (no high/critical advisories)');
  return 0;
}

process.exit(main());
