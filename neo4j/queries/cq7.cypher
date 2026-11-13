// CQ 7: Has a decision been made for event X? (example: E5)
// In OWL this is the defined class DecidedEvent (ComplianceEvent and hasDecision some Decision),
// inferred by a reasoner. Neo4j has no reasoner, so the definition is written as a query.
// Expected: false
MATCH (e:ComplianceEvent {uri: "https://anniechiang-data.framer.website/ontology/talentflow-sample#e5"})
RETURN e.label_en AS event,
       EXISTS { MATCH (e)-[:HAS_DECISION]->(:Decision) } AS decided;
