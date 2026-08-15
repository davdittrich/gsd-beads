---
created: 2026-08-10T14:22:00Z
title: Fix flaky retry loop in sync
area: sync
severity: major
files:
  - .gsd/capabilities/beads/scripts/sync.py:120-140
---

## Problem

The retry loop in sync.py occasionally double-submits a bd create call when bd is slow to
respond, producing a duplicate issue for the same task.

## Solution

Add a completed flag guarded before retrying, so a slow-but-eventually-successful call is never
retried after the fact.
