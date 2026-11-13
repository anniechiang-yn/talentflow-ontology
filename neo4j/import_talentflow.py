"""Import the TalentFlow sample data and the decision-status vocabulary into Neo4j.

Purpose:  Show how the RDF model maps to a labeled property graph (LPG).
Usage:    python neo4j/import_talentflow.py            # load into Neo4j
          python neo4j/import_talentflow.py --dry-run  # count only, no database
Input:    examples/talentflow-sample-data.ttl, imports/decision-status.ttl
Output:   Nodes and relationships in Neo4j; a summary printed to the terminal.
Connection settings come from environment variables:
          NEO4J_URI (default bolt://localhost:7687), NEO4J_USER (default neo4j),
          NEO4J_PASSWORD (required unless --dry-run).

Mapping (see neo4j/MAPPING.md):
  1. Each typed resource becomes a node with label Resource plus one label per class.
     Its full IRI is stored in the property uri (unique constraint).
  2. rdfs:label / skos:prefLabel become label_en and label_zh.
  3. Datatype properties become node properties (xsd:dateTime -> Neo4j DateTime).
  4. Object properties become relationships named in UPPER_SNAKE_CASE.
     tf:supersededBy is not stored: SUPERSEDES can be read in both directions.
  5. Decision statuses stay as Concept nodes so that skos:broader is kept.
  6. The ordered collection ds:DecisionProgression becomes a Collection node with
     MEMBER relationships that carry a position property.
  7. Defined classes (DecidedEvent, SupersededDecision) are not materialised:
     Neo4j has no reasoner, so they are written as queries instead.
Predicates not in the mapping are counted and reported, not silently dropped.
"""
import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.namespace import SKOS

TF = Namespace("https://anniechiang-data.framer.website/ontology/talentflow#")
REPO = Path(__file__).resolve().parent.parent
FILES = [REPO / "examples" / "talentflow-sample-data.ttl",
         REPO / "imports" / "decision-status.ttl"]

# RDF class -> Neo4j label
CLASS_LABELS = {
    TF.ComplianceEvent: "ComplianceEvent",
    TF.Decision: "Decision",
    TF.Actor: "Actor",
    TF.Regulation: "Regulation",
    TF.Document: "Document",
    SKOS.Concept: "Concept",
    SKOS.ConceptScheme: "ConceptScheme",
    SKOS.OrderedCollection: "Collection",
}
# RDF object property -> Neo4j relationship type
OBJECT_PROPERTIES = {
    TF.hasDecision: "HAS_DECISION",
    TF.hasDecisionStatus: "HAS_DECISION_STATUS",
    TF.basedOnRegulation: "BASED_ON_REGULATION",
    TF.involvesRegulation: "INVOLVES_REGULATION",
    TF.madeBy: "MADE_BY",
    TF.reportedBy: "REPORTED_BY",
    TF.hasResponsibleActor: "HAS_RESPONSIBLE_ACTOR",
    TF.hasDocument: "HAS_DOCUMENT",
    TF.supersedes: "SUPERSEDES",
    SKOS.broader: "BROADER",
    SKOS.related: "RELATED",
    SKOS.inScheme: "IN_SCHEME",
    SKOS.topConceptOf: "TOP_CONCEPT_OF",
}
# RDF datatype property -> Neo4j node property
DATA_PROPERTIES = {
    TF.decidedAt: "decidedAt",
    TF.hasDeadline: "deadline",
    TF.hasClosedDate: "closedDate",
    SKOS.notation: "notation",
}
# Language-tagged text -> two node properties
TEXT_PROPERTIES = {RDFS.label: "label", SKOS.prefLabel: "label", SKOS.definition: "definition"}
LANG_SUFFIX = {"en": "en", "zh-hant": "zh"}
# Inverse properties: not stored, the other direction already is
SKIPPED_INVERSES = {TF.supersededBy, SKOS.hasTopConcept}


def build(graph):
    """Turn the RDF graph into plain node and relationship lists."""
    nodes = {}
    for s, o in graph.subject_objects(RDF.type):
        if o in CLASS_LABELS and isinstance(s, URIRef):
            node = nodes.setdefault(str(s), {"labels": {"Resource"}, "props": {"uri": str(s)}})
            node["labels"].add(CLASS_LABELS[o])

    rels, skipped = [], Counter()
    handled = set(TEXT_PROPERTIES) | set(DATA_PROPERTIES) | set(OBJECT_PROPERTIES) | {RDF.type, SKOS.memberList}
    for s, p, o in graph:
        if str(s) not in nodes:
            continue
        props = nodes[str(s)]["props"]
        if p in TEXT_PROPERTIES and isinstance(o, Literal):
            suffix = LANG_SUFFIX.get((o.language or "").lower())
            if suffix:
                props[f"{TEXT_PROPERTIES[p]}_{suffix}"] = str(o)
        elif p in DATA_PROPERTIES and isinstance(o, Literal):
            props[DATA_PROPERTIES[p]] = o.toPython()
        elif p in OBJECT_PROPERTIES and str(o) in nodes:
            rels.append((str(s), OBJECT_PROPERTIES[p], str(o), {}))
        elif p == SKOS.memberList:
            for position, member in enumerate(Collection(graph, o), start=1):
                rels.append((str(s), "MEMBER", str(member), {"position": position}))
        elif p in SKIPPED_INVERSES:
            skipped[f"{graph.qname(p)} (inverse, not stored)"] += 1
        elif p not in handled:
            skipped[graph.qname(p)] += 1
    return nodes, rels, skipped


def load(nodes, rels, uri, user, password):
    """Write nodes and relationships with MERGE, so the script can be re-run."""
    from neo4j import GraphDatabase
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()  # fail fast on a wrong password or a stopped instance
        driver.execute_query(
            "CREATE CONSTRAINT resource_uri IF NOT EXISTS "
            "FOR (r:Resource) REQUIRE r.uri IS UNIQUE")
        for node in nodes.values():
            # Labels cannot be query parameters; they come from the fixed CLASS_LABELS map.
            labels = ":".join(sorted(node["labels"]))
            driver.execute_query(
                f"MERGE (n:Resource {{uri: $uri}}) SET n:{labels} SET n += $props",
                uri=node["props"]["uri"], props=node["props"])
        for start, rel_type, end, props in rels:
            # Relationship types come from the fixed OBJECT_PROPERTIES map.
            driver.execute_query(
                f"MATCH (a:Resource {{uri: $start}}), (b:Resource {{uri: $end}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props",
                start=start, end=end, props=props)
        records, _, _ = driver.execute_query(
            "MATCH (n:Resource) RETURN count(n) AS nodes, "
            "COUNT { MATCH (:Resource)-[]->(:Resource) } AS rels")
        return records[0]["nodes"], records[0]["rels"]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="count only, do not connect")
    args = parser.parse_args()

    graph = Graph()
    for path in FILES:
        graph.parse(path)
    nodes, rels, skipped = build(graph)

    print(f"RDF triples read: {len(graph)}")
    print(f"Nodes to write: {len(nodes)}")
    for label, n in sorted(Counter(l for v in nodes.values() for l in v["labels"] if l != "Resource").items()):
        print(f"  {label}: {n}")
    print(f"Relationships to write: {len(rels)}")
    for rel_type, n in sorted(Counter(r[1] for r in rels).items()):
        print(f"  {rel_type}: {n}")
    print("Predicates not imported:")
    for name, n in sorted(skipped.items()):
        print(f"  {name}: {n}")

    if args.dry_run:
        return 0
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        print("ERROR: set NEO4J_PASSWORD first (see README).", file=sys.stderr)
        return 1
    from neo4j.exceptions import AuthError, ServiceUnavailable
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    try:
        n_nodes, n_rels = load(nodes, rels, uri,
                               os.environ.get("NEO4J_USER", "neo4j"), password)
    except AuthError:
        print("ERROR: Neo4j rejected the user name or password.", file=sys.stderr)
        return 1
    except ServiceUnavailable:
        print(f"ERROR: cannot reach Neo4j at {uri}. Is the instance running?", file=sys.stderr)
        return 1
    print(f"In Neo4j now: {n_nodes} Resource nodes, {n_rels} relationships")
    ok = n_nodes == len(nodes) and n_rels == len(rels)
    print("Check: counts match" if ok else "Check: counts DIFFER, see above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
