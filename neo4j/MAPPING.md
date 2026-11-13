# RDF to Neo4j mapping

How `import_talentflow.py` turns the TalentFlow sample data and the decision-status vocabulary into a labeled property graph (LPG).

| RDF | Neo4j | Example |
|---|---|---|
| Resource IRI | Node property `uri`, unique constraint on `:Resource(uri)` | `uri = ".../talentflow-sample#d2c"` |
| `rdf:type` (class) | Label `Resource` plus one label per class | `:Resource:Decision` |
| `rdfs:label`, `skos:prefLabel` | `label_en`, `label_zh` | `label_en = "Decided"` |
| `skos:definition` | `definition_en`, `definition_zh` | |
| Datatype property | Node property (`xsd:dateTime` becomes Neo4j `DateTime`) | `decidedAt`, `deadline`, `closedDate` |
| Object property | Relationship in UPPER_SNAKE_CASE | `tf:hasDecision` becomes `HAS_DECISION` |
| `tf:supersededBy`, `skos:hasTopConcept` | Not stored | The inverse relationship is already stored and can be traversed both ways |
| `skos:Concept` (decision status) | `:Concept` node, `BROADER` relationships kept | `(d)-[:HAS_DECISION_STATUS]->(:Concept)` |
| `skos:OrderedCollection` + `skos:memberList` | `:Collection` node, `MEMBER` relationships with `position` | `DecisionProgression -[:MEMBER {position: 1}]-> Exploring` |
| Defined classes `DecidedEvent`, `SupersededDecision` | Not stored | Neo4j has no OWL reasoner; these are written as Cypher queries |

## Design decisions

- **Statuses as nodes, not strings.** Keeping `skos:broader` lets a query select every status under a broader concept, as CQ 16 does in SPARQL.
- **Defined classes as queries.** Precomputing them with a reasoner before import would hide the main difference between RDF and an LPG: in Neo4j, what is not stored has to be derived in the query.
- **Two label properties instead of language tags.** An LPG property holds one value with no language tag, so each language gets its own property.
- **The ordered collection uses a relationship property.** In RDF the order is an `rdf:first`/`rdf:rest` list; in Neo4j it is a `position` on each `MEMBER` relationship.

## Not imported

Ontology headers (`dct:*`, `owl:versionInfo`) and documentation notes on concepts (`skos:altLabel`, `skos:scopeNote`, `skos:example`, `skos:note`, `skos:historyNote`, `skos:changeNote`, `skos:editorialNote`). The script lists their counts on every run, so nothing is dropped silently.

## Expected counts

37 nodes (6 ComplianceEvent, 8 Decision, 4 Actor, 5 Regulation, 4 Document, 8 Concept, 1 ConceptScheme, 1 Collection) and 77 relationships, from 303 RDF triples.
