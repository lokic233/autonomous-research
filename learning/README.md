# learning/ — Global cross-session lessons for ALL research agents

This folder is **NOT session-scoped**. Every agent working in this repo — on any node, any date —
should read it BEFORE running experiments. It exists because mistakes here cost real hardware time
and real money. Add to it whenever you learn something the hard way.

## Index
- **`MI350X_CRASH_POSTMORTEM.md`** — how a single agent crashed the AMD MI350X devgpu **three times**
  in one session (one triggered a 4–5 hour hardware repair). Read before touching ANY GPU VMM probe.

## The one rule that would have prevented most of this
> **If a result will not change a decision/vote, do not run the experiment.**
> Gilding an already-validated result is how you turn zero risk into a crashed node.
