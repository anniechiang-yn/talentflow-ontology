# Competency question validation (SPARQL)

All 16 competency questions are answered by the queries in this folder, run against `../examples/talentflow-sample-data.ttl` (fictional data) in GraphDB 11.4 with the OWL 2 RL (Optimized) ruleset. Verified on 2026-11-04.

| CQ | Question | Query | Example | Result | Needs inference |
|---|---|---|---|---|---|
| 1 | What is the current decision status of event X? | `cq1.rq` | E4 | D4b, Exploring | No |
| 2 | Which events are overdue and still open? | `cq2.rq` | — | E2 | No |
| 3 | How many events are there under each decision status? | `cq3.rq` | — | Decided 2, Implemented 1, Exploring 1, Abandoned 1 | No |
| 4 | Which events are due within the next 7 days? | `cq4.rq` | run on 2026-11-04 | E1 | No |
| 5 | Which open events is a given actor responsible for? | `cq5.rq` | Data Protection Officer | E1 | No |
| 6 | Which events have no responsible actor assigned? | `cq6.rq` | — | E4 | No |
| 7 | Has a decision been made for event X? | `cq7.rq` | E5 | No (false) | Yes (`DecidedEvent`) |
| 8 | What is the current status of every event reported by a given actor? | `cq8.rq` | HR department | E1 Decided, E3 Implemented, E5 none, E6 Abandoned | No |
| 9 | What is the full decision history of event X, in time order? | `cq9.rq` | E2 | D2a, D2b (superseded), D2c (current) | No |
| 10 | Which decisions replaced decision D, along the full chain? | `cq10.rq` | D2a | D2b, D2c | No |
| 11 | Who made decision D, and when? | `cq11.rq` | D2c | Data Protection Officer, 2026-10-31 | No |
| 12 | Which regulations is decision D based on? | `cq12.rq` | D2c | Art. 33, Art. 34 | No |
| 13 | Which documents are linked to event X? | `cq13.rq` | E2 | 2 documents | No |
| 14 | Which events involve a given article? | `cq14.rq` | Art. 33 | E2, E6 | No |
| 15 | Which events have a status under a given broader concept? | `cq15.rq` | Decision-bearing | E1, E2, E3, E4, E6 | No |
| 16 | Which decisions in force (not superseded, rejected or abandoned) are based on a given article? | `cq16.rq` | Art. 33 | D2c (E2) | No |

`construct-open-events.rq` is an extra CONSTRUCT example that extracts open events with their deadline and responsible actor as a sub-graph.

## Definitions used across queries

- **Open event**: has no `hasClosedDate` (CQ 2, 5).
- **Current status of an event**: the status of its most recent decision by `decidedAt`; each event is counted once (CQ 1, 3, 8).
- **Decision in force**: not the object of any `supersedes`, and its status is a member of `ds:DecisionProgression` (Exploring, Decided, Implemented) (CQ 16).

## Why most answers come from SPARQL rather than the reasoner

- Questions about absence (no closing date, no responsible actor, not superseded) need a closed-world check (`FILTER NOT EXISTS`). OWL reasoning assumes an open world and cannot conclude that something is missing.
- Questions about the current date (overdue, due soon) need `NOW()`, which OWL has no equivalent for.
- The reasoner is used where a class can be defined from what is present: `DecidedEvent` (CQ 7) and `SupersededDecision`.

## Notes found while testing

- GraphDB stores the language tag `zh-hant` as `zh-Hant`. Exact comparison `LANG(?x) = "zh-hant"` returns nothing; use `LANGMATCHES`.
- Version 1.0.0 defined `SupersededDecision` with an anonymous inverse property. HermiT inferred it but GraphDB's OWL 2 RL ruleset did not. Version 1.1.0 uses the named inverse `supersededBy`.
- With the RDFS-Plus ruleset neither defined class is inferred.
