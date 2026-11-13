// CQ 1: What is the current decision status of event X? (example: E4)
// Current status = status of the event's latest decision by decidedAt (same definition as SPARQL cq1.rq).
// Expected: D4b, Exploring
MATCH (e:ComplianceEvent {uri: "https://anniechiang-data.framer.website/ontology/talentflow-sample#e4"})-[:HAS_DECISION]->(d:Decision)-[:HAS_DECISION_STATUS]->(s:Concept)
WHERE d.decidedAt IS NOT NULL
  AND NOT EXISTS {
    MATCH (e)-[:HAS_DECISION]->(other:Decision)
    WHERE other.decidedAt > d.decidedAt
  }
RETURN d.label_en AS decision, s.label_en AS status, d.decidedAt AS decidedAt;
