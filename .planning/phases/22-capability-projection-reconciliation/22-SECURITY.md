---
phase: 22-capability-projection-reconciliation
audited_head: ed547388ecfc3fa8ce7d35cbed795337b02c4bb4
verdict: SECURED
asvs_level: 1
threats_closed: 7
threats_open: 0
accepted_risks: 0
---

# Phase 22 Security Verification

## Verdict

SECURED. All seven registered threats are closed at
`ed547388ecfc3fa8ce7d35cbed795337b02c4bb4`; there are no accepted risks.

## Threat Closure

| Threat | Boundary | Evidence | Status | Confidence |
|---|---|---|---|---:|
| T-22-01 | Hook transaction lock | The wrapper acquires nonblocking `fcntl.flock`; the locked child validates FD 9 identity, ownership, type, inode, device, and link count, then independently confirms `LOCK_EX | LOCK_NB` before projection. Cases 12, 12a, 12b, 15, and 16 cover forged state, inherited confirmation, contention, descriptor isolation, and crash release. | CLOSED | 99/100 |
| T-22-02 | Selected-skill ownership | The pre-native guard rejects symlinked owner markers. Case 18 proves preservation and zero native writes. | CLOSED | 100/100 |
| T-22-03 | Ledger publication | Existing targets are type-checked; a secure same-directory temporary is flushed and fsynced before atomic `os.replace`; eligible legacy state is removed only after canonical success. Cases 19 through 21b cover ordering and failure preservation. | CLOSED | 100/100 |
| T-22-04 | Diagnostics and contention | Lock-helper stderr is suppressed and mapped to fixed diagnostics; contention exits before projection. Case 17 proves hostile multiline output is bounded. | CLOSED | 100/100 |
| T-22-05 | Non-cooperating external writer | Final observations reject already-visible drift. The documented boundary is deliberately non-atomic for direct writers; case 23b proves later drift invalidates the receipt and is repaired on the next SessionStart. | CLOSED | 99/100 |
| T-22-06 | Runtime and path authority | Runtime selection is allowlisted, the public skills root must equal the canonical destination, and selected writes are delegated only to native gsd-core install/set. User, sibling, unrelated, and unselected-runtime state is preserved. | CLOSED | 99/100 |
| T-22-SC | CI supply and provenance | CI checks out public gsd-core `v1.12.0`, verifies exact runtime identity, and runs the smoke harness. The real fixture separately proves immutable v1.10.0 compatibility provenance and genuine stale-generation repair. | CLOSED | 99/100 |

## Prior Blockers

The marker-symlink bypass and unsafe ledger publication are closed by the
controls above. The PID/symlink/quarantine stale-takeover protocol was deleted;
kernel descriptor lifetime now releases the lock after normal exit or crash.

## Ponytail Assessment

The implementation uses the existing Python standard library and native
gsd-core writers. It adds no dependency, polling loop, PID registry, stale-lock
takeover, custom projector, or cross-runtime copier.

**threats_open:** 0
