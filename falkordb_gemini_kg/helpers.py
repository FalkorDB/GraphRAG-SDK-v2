import re
from falkordb_gemini_kg.classes.ontology import Ontology

def extract_json(text: str):
    regex = r"```(?:json)?(.*?)```"
    matches = re.findall(regex, text, re.DOTALL)

    return "".join(matches)


def map_dict_to_cypher_properties(d: dict):
    cypher = "{"
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


def verify_cypher_labels(cypher: str, ontology: Ontology):
    try:
        if not cypher or len(cypher) == 0:
            return "Cypher statement is empty"

        not_found_node_labels = []
        node_labels = re.findall(r"\(:(.*?)\)", cypher)
        for label in node_labels:
            label = label.split(":")[1] if ":" in label else label
            label = label.split("{")[0].strip() if "{" in label else label
            if label not in [node.label for node in ontology.nodes]:
                not_found_node_labels.append(label)

        not_found_edge_labels = []
        edge_labels = re.findall(r"\[:(.*?)\]", cypher)
        for label in edge_labels:
            label = label.split(":")[1] if ":" in label else label
            label = label.split("{")[0].strip() if "{" in label else label
            if label not in [edge.label for edge in ontology.edges]:
                not_found_edge_labels.append(label)

        if len(not_found_node_labels) > 0 or len(not_found_edge_labels) > 0:
            return f"""
    The following labels were not found in the ontology:
    Nodes: {set(not_found_node_labels)}
    Edges: {set(not_found_edge_labels)}
    """
        return True
    except Exception as e:
        print(f"Failed to verify cypher labels: {e}")
        return e
