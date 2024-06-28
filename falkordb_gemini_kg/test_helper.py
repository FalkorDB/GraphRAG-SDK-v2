import re
from falkordb_gemini_kg.classes.ontology import Edge, Ontology
import json

cypher = """
MATCH (f:Fighter)-[r:FOUGHT_IN]->(fight:Fight)
RETURN f, count(fight) AS fight_count
ORDER BY fight_count DESC
LIMIT 1"""


ontology_file = "falkordb_gemini_kg/demos/ufc_ontology_corrected.json"
with open(ontology_file, "r", encoding="utf-8") as file:
    ontology = Ontology.from_json(json.loads(file.read()))


def validate_cypher(edges, ontology: Ontology):
    errors = []
    edges = list(re.finditer(r"\[.*?\]", cypher))
    i = 0
    for edge in edges:
        try:
            edge_label_match = re.search(r"(?:\[)(?:\w)*(?:\:)([^{\]]+)", edge.group(0))
            if edge_label_match is None:
                raise Exception("Edge label not found")
            edge_label = edge_label_match.group(1).strip()
            print(edge_label)
            prev_edge = edges[i - 1] if i > 0 else None
            next_edge = edges[i + 1] if i < len(edges) - 1 else None
            before = (
                cypher[prev_edge.end() : edge.start()]
                if prev_edge
                else cypher[: edge.start()]
            )
            rel_before = re.search(r"([^\)\]]+)", before[::-1]).group(0)[::-1]
            print(rel_before)
            after = (
                cypher[edge.end() : next_edge.start()]
                if next_edge
                else cypher[edge.end() :]
            )
            rel_after = re.search(r"([^\(\[]+)", after).group(0)
            print(rel_after)
            node_before = re.search(r"\(.+:(.*?)\)", before).group(0)
            print(node_before)
            node_after = re.search(r"\(([^\)]+)(\)?)", after).group(0)
            print(node_after)
            if rel_before == "-" and rel_after == "->":
                source = node_before
                target = node_after
            elif rel_before == "<-" and rel_after == "-":
                source = node_after
                target = node_before
            else:
                continue

            source_label = re.search(r"(?:\:)([^\)\{]+)", source).group(1).strip()
            print(source_label)
            target_label = re.search(r"(?:\:)([^\)\{]+)", target).group(1).strip()
            print(target_label)
            ontology_edge = ontology.get_edge_with_label(edge_label)

            if ontology_edge is None:
                errors.append(f"Edge {edge_label} not found in ontology")

            if (
                not ontology_edge.source.label == source_label
                or not ontology_edge.target.label == target_label
            ):
                errors.append(
                    f"Edge {edge_label} has a mismatched source or target. Make sure the edge direction is correct. The edge should connect {ontology_edge.source.label} to {ontology_edge.target.label}."
                )

            i += 1
        except Exception as e:
            errors.append(str(e))
            continue

    return errors


print(validate_cypher(cypher, ontology))
