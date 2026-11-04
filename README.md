# TalentFlow Compliance Ontology

An OWL 2 ontology for tracking GDPR compliance events, the decisions made about them, and the chain of decisions that replace one another. The setting is TalentFlow B.V., a fictional 50-person talent-management SaaS company headquartered in Berlin.

Version 1.1.0 · Licence CC BY 4.0 · Author: Annie Chiang

## What it is for

The compliance lead, HR, auditors and an AI retrieval layer need to answer questions such as:

- What is the current status of an event, who is responsible, and when is it due?
- What is the full decision history of an event, including decisions that were later replaced?
- Which decisions are still in force for a given GDPR article?

The ontology is scoped by 16 competency questions (below). Labels and comments are bilingual (English and Traditional Chinese).

## Files

| File | Purpose |
|---|---|
| `talentflow.ttl` | The ontology (classes, properties, definitions) |
| `talentflow-test.ttl` | Test individuals that check the reasoner's classifications |
| `imports/decision-status.ttl` | Pinned copy of the Decision Status Vocabulary v1.1.0 (SKOS), used for status values |
| `catalog-v001.xml` | Tells Protégé where to find imported ontologies locally |

## Model at a glance

Classes: `ComplianceEvent`, `Decision`, `Regulation` (GDPR articles as individuals), `Actor`, `Document`, and two defined classes inferred by the reasoner:

- `DecidedEvent` ≡ ComplianceEvent and (hasDecision some Decision)
- `SupersededDecision` ≡ Decision and (supersededBy some Decision)

Key properties: `hasDecision`, `supersedes` (new → old) and its inverse `supersededBy` (old → new, inferred), `hasDecisionStatus` (values from the SKOS vocabulary), `madeBy`, `basedOnRegulation`, `involvesRegulation`, `hasResponsibleActor`, `reportedBy`, `hasDocument`, `decidedAt`, `hasDeadline`, `hasClosedDate`.

## Key design decisions

1. Status values are SKOS concepts, not OWL subclasses. Status is a value that changes over time, not a kind of decision. Using a controlled vocabulary keeps the class hierarchy stable and lets queries walk the vocabulary's broader/narrower structure.
2. "Superseded" has one source of truth: the `supersedes` relation. `hasDecisionStatus` records only the stage a decision reached (Exploring, Decided, Implemented) or how it ended without replacement (Abandoned, Rejected). Whether a decision has been superseded is inferred, so a manually set status can never contradict the relation.
3. `hasDecisionStatus` is not declared functional. OWL has no unique-name assumption, so a functional property with two values would make the reasoner merge the two concepts instead of reporting an error. The one-value rule will be enforced with SHACL (`sh:maxCount 1`).
4. The inverse of `supersedes` is a named property. Version 1.0.0 defined `SupersededDecision` with an anonymous inverse (`inverse supersedes`). HermiT in Protégé classified it correctly, but GraphDB with the OWL 2 RL ruleset did not. Declaring `supersededBy` as a named `owl:inverseOf` property gives the same result in both. Other properties still have no declared inverse; inverse lookups are done in SPARQL.
5. Questions that depend on absence or on the current date are answered at the query layer. Under the open-world assumption, the reasoner cannot conclude that something is missing (for example "no responsible actor" or "not superseded"), and OWL 2 cannot compare a deadline with today's date. These are handled in SPARQL.

## Competency questions

| # | Question | Answered by |
|---|---|---|
| 1 | What is the current decision status of event X? | Query |
| 2 | Which events are overdue and still open? | Query (`NOW()`) |
| 3 | How many events are there under each decision status? | Query (`COUNT`) |
| 4 | Which events are due within the next 7 days? | Query (`NOW()`) |
| 5 | Which open events is a given actor responsible for? | Query |
| 6 | Which events have no responsible actor assigned? | Query (`FILTER NOT EXISTS`) |
| 7 | Has a decision been made for event X? | Reasoner (`DecidedEvent`) |
| 8 | What is the current status of every event reported by a given person? | Query |
| 9 | What is the full decision history of event X, in time order, including superseded decisions? | Query |
| 10 | Which decision superseded decision D, and what is the full chain? | Reasoner (`SupersededDecision`) + query (property path) |
| 11 | Who made decision D, and when? | Query |
| 12 | Which regulations is decision D based on? | Query |
| 13 | Which documents are linked to event X? | Query |
| 14 | Which events involve a given article (e.g. Art. 33)? | Query |
| 15 | Which events have a status under a given broader concept (e.g. Decision-bearing)? | Query (SKOS property path) |
| 16 | Which decisions currently in force (not superseded, not rejected) involve a given article? | Query (`FILTER NOT EXISTS`) |

## How to open and check it

1. Open `talentflow-test.ttl` in [Protégé](https://protege.stanford.edu/) 5.6 or later. The catalog file resolves the imports from this folder.
2. Run Reasoner → HermiT → Start reasoner.
3. Expected results: `testEvent1` is classified as a Decided event; `testDecision1` as a Superseded decision; `testDecision2` stays a plain Decision.

## Status and roadmap

- v1.0.0: OWL model, defined classes, SKOS status layer, reasoner tests (done)
- v1.1.0: named inverse property `supersededBy`, so that `SupersededDecision` is also inferred in GraphDB (done)
- Next: SPARQL queries for all 16 competency questions, SHACL validation, and use as a semantic layer for retrieval (GraphRAG)

## Related

- [Decision Status Vocabulary (SKOS)](https://github.com/anniechiang-yn/decision-status-skos), the source of status values. The canonical version lives in its own repository; `imports/` holds a pinned copy of version 1.1.0.
