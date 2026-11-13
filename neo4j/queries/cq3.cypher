// CQ 3: How many events are there under each decision status?
// Each event is counted once, by the status of its latest decision.
// Cypher has no GROUP BY: status is the grouping key because it is not aggregated.
// Expected: Decided 2, Implemented 1, Exploring 1, Abandoned 1
MATCH (e:ComplianceEvent)-[:HAS_DECISION]->(d:Decision)-[:HAS_DECISION_STATUS]->(s:Concept)
WHERE d.decidedAt IS NOT NULL
  AND NOT EXISTS {
    MATCH (e)-[:HAS_DECISION]->(other:Decision)
    WHERE other.decidedAt > d.decidedAt
  }
RETURN s.label_en AS status, count(DISTINCT e) AS events
ORDER BY events DESC, status;
