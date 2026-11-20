# Retired frontend audit exception for picomatch

GitHub withdrew GHSA-fc5q-39xc-vjpf on 18 November 2026. At retirement, the
frontend lockfile and npm registry both reported picomatch 4.0.7, and the
unfiltered frontend audit reported zero vulnerabilities. The lockfile retains
the same dependency versions. [GitHub advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)

The CI audit now blocks every high or critical finding, including this
advisory if it is reported again. Registry and network errors, inconsistent
exit status, and invalid audit reports still block the gate. Run the same
checks locally with:

```sh
npm --prefix frontend audit --audit-level=high
node scripts/frontend_security_audit.mjs
node --test scripts/frontend_security_audit.test.mjs
```

The original exception and owner decision are recorded in issue #36. The
previous expiry was 18 December 2026. [GHSA exception tracking issue](https://github.com/nguyendodary/DBCAS/issues/36)
