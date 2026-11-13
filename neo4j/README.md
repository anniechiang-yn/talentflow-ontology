# TalentFlow in Neo4j

The same fictional TalentFlow data, loaded into Neo4j as a labeled property graph (LPG), and five of the sixteen competency questions answered in Cypher. The aim is to compare the two models on the same data, not to replace the RDF version.

## Limitations

- Fictional sample data only: 37 nodes and 77 relationships. Nothing here says anything about performance.
- Five competency questions were rewritten (CQ 1, 3, 7, 10, 16), not all sixteen.
- Neo4j has no OWL reasoner. The defined class `DecidedEvent` (CQ 7) is written as a query, so if the ontology definition changes, the query has to be changed by hand.
- Run with Neo4j Desktop 2.3.1 (Cypher 25), Python 3.13, rdflib 7.6.0 and the neo4j driver 6.4.1. Other versions were not tested.

## What was checked

- Import: 303 RDF triples became 37 nodes and 77 relationships; the counts in Neo4j match the counts the script expects (the script checks this itself).
- Queries: the five Cypher queries return the same answers as the SPARQL queries in [`../queries/RESULTS.md`](../queries/RESULTS.md).

| CQ | Question | Cypher | SPARQL | Same answer |
|---|---|---|---|---|
| 1 | Current decision status of E4 | D4b, Exploring | D4b, Exploring | Yes |
| 3 | Events per decision status | Decided 2, Abandoned 1, Exploring 1, Implemented 1 | Decided 2, Implemented 1, Exploring 1, Abandoned 1 | Yes (ties sorted differently) |
| 7 | Has a decision been made for E5? | false | false | Yes |
| 10 | Decisions that replaced D2a | D2b, D2c | D2b, D2c | Yes |
| 16 | Decisions in force based on Art. 33 | D2c (E2), Decided | D2c (E2), Decided | Yes |

## RDF and LPG on the same data

| | RDF (`../talentflow.ttl`) | LPG (Neo4j) |
|---|---|---|
| Identity | Every resource has a global IRI | No IRI; internal IDs can be reused after deletion, so the IRI is stored in `uri` with a unique constraint |
| Types | Classes with a subclass hierarchy | Labels, several per node, with no hierarchy |
| Facts about a relationship | Need an extra node or RDF-star | Stored directly as relationship properties (used for `MEMBER.position`) |
| Inference | OWL reasoner classifies `DecidedEvent` | No reasoner; the definition becomes a query |
| Validation | SHACL (closed world) | Constraints (unique, required, type) |
| Paths | `tf:supersedes+` returns the end points | `[:SUPERSEDES*]` can also return the whole path |

In this project RDF stays the source of truth for meaning and governance (shared IRIs, a published vocabulary, reasoning, SHACL). The LPG copy shows how the same model serves application-style queries.

## Run it

Needs Neo4j Desktop with a running local instance.

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install rdflib neo4j
python neo4j/import_talentflow.py --dry-run      # counts only
read -s NEO4J_PASSWORD && export NEO4J_PASSWORD  # password is not echoed or saved to history
python neo4j/import_talentflow.py
```

Then run the files in `queries/` in the Neo4j Query tool. Mapping details are in [`MAPPING.md`](MAPPING.md).

## Files

- `import_talentflow.py`: reads the sample data and the decision-status vocabulary, writes nodes and relationships with `MERGE`, and checks the counts.
- `MAPPING.md`: how each RDF construct maps to the LPG, and why.
- `queries/cq*.cypher`: the five competency questions in Cypher.
