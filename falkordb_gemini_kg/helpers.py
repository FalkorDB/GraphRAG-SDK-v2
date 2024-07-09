import re
import falkordb_gemini_kg
import logging
from fix_busted_json import repair_json

logger = logging.getLogger(__name__)


def extract_json(text: str):
    regex = r"(?:```)?(?:json)?([^`]*)(?:\\n)?(?:```)?"
    matches = re.findall(regex, text, re.DOTALL)

    return repair_json("".join(matches))


def map_dict_to_cypher_properties(d: dict):
    cypher = "{"
    if isinstance(d, list):
        if len(d) == 0:
            return "{}"
        for i, item in enumerate(d):
            cypher += f"{i}: {item}, "
        cypher = (cypher[:-2] if len(cypher) > 1 else cypher) + "}"
        return cypher
    for key, value in d.items():
        # Check value type
        if isinstance(value, str):
            # Find unescaped quotes
            reg = r"((?<!\\)(\"))|((?<!\\)(\'))"
            search = re.search(reg, value)
            if search:
                i = 0
                for match in re.finditer(reg, value):
                    value = (
                        value[: match.start() + i] + "\\" + value[match.start() + i :]
                    )
                    i += 1
            value = f'"{value}"' if f"{value}" != "None" else '""'
        else:
            value = str(value) if f"{value}" != "None" else '""'
        cypher += f"{key}: {value}, "
    cypher = (cypher[:-2] if len(cypher) > 1 else cypher) + "}"
    return cypher


def stringify_falkordb_response(response):
    if not isinstance(response, list) or len(response) == 0:
        data = str(response).strip()
    elif not isinstance(response[0], list):
        data = str(response).strip()
    else:
        for l, _ in enumerate(response):
            if not isinstance(response[l], list):
                response[l] = str(response[l])
            else:
                for i, __ in enumerate(response[l]):
                    response[l][i] = str(response[l][i])
        data = str(response).strip()

    return data


def extract_cypher(text: str):

    if not text.startswith("```"):
        return text

    regex = r"```(?:cypher)?(.*?)```"
    matches = re.findall(regex, text, re.DOTALL)

    return "".join(matches)


def validate_cypher(
    cypher: str, ontology: falkordb_gemini_kg.Ontology
) -> list[str] | None:
    try:
        if not cypher or len(cypher) == 0:
            return ["Cypher statement is empty"]

        errors = []

        # Check if nodes exist in ontology
        errors.extend(validate_cypher_nodes_exist(cypher, ontology))

        # Check if edges exist in ontology
        errors.extend(validate_cypher_edges_exist(cypher, ontology))

        # Check if edge directions are correct
        errors.extend(validate_cypher_edge_directions(cypher, ontology))

        if len(errors) > 0:
            return errors

        return None
    except Exception as e:
        print(f"Failed to verify cypher labels: {e}")
        return None


def validate_cypher_nodes_exist(cypher: str, ontology: falkordb_gemini_kg.Ontology):
    # Check if nodes exist in ontology
    not_found_node_labels = []
    node_labels = re.findall(r"\(:(.*?)\)", cypher)
    for label in node_labels:
        label = label.split(":")[1] if ":" in label else label
        label = label.split("{")[0].strip() if "{" in label else label
        if label not in [node.label for node in ontology.nodes]:
            not_found_node_labels.append(label)

    return [f"Node {label} not found in ontology" for label in not_found_node_labels]


def validate_cypher_edges_exist(cypher: str, ontology: falkordb_gemini_kg.Ontology):
    # Check if edges exist in ontology
    not_found_edge_labels = []
    edge_labels = re.findall(r"\[:(.*?)\]", cypher)
    for label in edge_labels:
        label = label.split(":")[1] if ":" in label else label
        label = label.split("{")[0].strip() if "{" in label else label
        if label not in [edge.label for edge in ontology.edges]:
            not_found_edge_labels.append(label)

    return [f"Edge {label} not found in ontology" for label in not_found_edge_labels]


def validate_cypher_edge_directions(cypher: str, ontology: falkordb_gemini_kg.Ontology):

    errors = []
    edges = list(re.finditer(r"\[.*?\]", cypher))
    i = 0
    for edge in edges:
        try:
            edge_label = (
                re.search(r"(?:\[)(?:\w)*(?:\:)([^{\]]+)", edge.group(0))
                .group(1)
                .strip()
            )
            prev_edge = edges[i - 1] if i > 0 else None
            next_edge = edges[i + 1] if i < len(edges) - 1 else None
            before = (
                cypher[prev_edge.end() : edge.start()]
                if prev_edge
                else cypher[: edge.start()]
            )
            rel_before = re.search(r"([^\)\]]+)", before[::-1]).group(0)[::-1]
            after = (
                cypher[edge.end() : next_edge.start()]
                if next_edge
                else cypher[edge.end() :]
            )
            rel_after = re.search(r"([^\(\[]+)", after).group(0)
            node_before = re.search(r"\(.+:(.*?)\)", before).group(0)
            node_after = re.search(r"\(([^\)]+)(\)?)", after).group(0)
            if rel_before == "-" and rel_after == "->":
                source = node_before
                target = node_after
            elif rel_before == "<-" and rel_after == "-":
                source = node_after
                target = node_before
            else:
                continue

            source_label = re.search(r"(?:\:)([^\)\{]+)", source).group(1).strip()
            target_label = re.search(r"(?:\:)([^\)\{]+)", target).group(1).strip()

            ontology_edges = ontology.get_edges_with_label(edge_label)

            if len(ontology_edges) == 0:
                errors.append(f"Edge {edge_label} not found in ontology")

            found_edge = False
            for ontology_edge in ontology_edges:
                if (
                    ontology_edge.source.label == source_label
                    and ontology_edge.target.label == target_label
                ):
                    found_edge = True
                    break

            if not found_edge:
                errors.append(
                    """
                    Edge {edge_label} does not connect {source_label} to {target_label}. Make sure the edge direction is correct. 
                    Valid edges: 
                    {valid_edges}
""".format(
                        edge_label=edge_label,
                        source_label=source_label,
                        target_label=target_label,
                        valid_edges="\n".join([str(e) for e in ontology_edges]),
                    )
                )

            i += 1
        except Exception as e:
            # errors.append(str(e))
            continue

    return errors
