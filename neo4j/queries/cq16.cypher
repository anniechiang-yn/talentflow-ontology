// CQ 16: Which decisions in force are based on a given article? (example: GDPR Art. 33)
// In force = not superseded, and the status is a member of DecisionProgression (Exploring, Decided, Implemented).
// Expected: D2c (E2), Decided
MATCH (e:ComplianceEvent)-[:HAS_DECISION]->(d:Decision)-[:BASED_ON_REGULATION]->(:Regulation {uri: "https://anniechiang-data.framer.website/ontology/talentflow-sample#gdprArt33"}),
      (d)-[:HAS_DECISION_STATUS]->(s:Concept)<-[:MEMBER]-(:Collection {uri: "https://anniechiang-data.framer.website/vocab/decision-status#DecisionProgression"})
WHERE NOT EXISTS { MATCH (:Decision)-[:SUPERSEDES]->(d) }
RETURN e.label_en AS event, d.label_en AS decision, s.label_en AS status
ORDER BY event;
