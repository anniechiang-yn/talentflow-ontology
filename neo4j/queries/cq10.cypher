// CQ 10: Which decisions replaced decision D, along the full chain? (example: D2a)
// [:SUPERSEDES*] follows the relationship one or more steps, like tf:supersedes+ in SPARQL.
// The arrow points into D2a because later decisions supersede earlier ones.
// Expected: D2b, D2c
MATCH (start:Decision {uri: "https://anniechiang-data.framer.website/ontology/talentflow-sample#d2a"})<-[:SUPERSEDES*]-(later:Decision)
RETURN later.label_en AS decision, later.decidedAt AS decidedAt
ORDER BY decidedAt;
