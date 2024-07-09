import json
import logging
from .attribute import Attribute, AttributeType
from falkordb import Node as GraphNode
import re
logger = logging.getLogger(__name__)

descriptionKey = "__description__"

class Node:
    def __init__(self, label: str, attributes: list[Attribute], description: str = ""):
        self.label = re.sub(r"([^a-zA-Z0-9_])", "", label)
        self.attributes = attributes
        self.description = description

    @staticmethod
    def from_graph(node: GraphNode):
        logger.debug(f"Node.from_graph: {node}")
        return Node(
            node.labels[0],
            [
                Attribute(
                    attr,
                    AttributeType.fromString(node.properties[attr]),
                    "!" in node.properties[attr],
                )
                for attr in node.properties if attr != descriptionKey
            ],
            node.properties[descriptionKey] if descriptionKey in node.properties else "",
        )

    @staticmethod
    def from_json(txt: dict | str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Node(
            txt["label"],
            [
                Attribute.from_json(attr)
                for attr in (txt["attributes"] if "attributes" in txt else [])
            ],
            txt["description"] if "description" in txt else "",
        )

    def to_json(self):
        return {
            "label": self.label,
            "attributes": [attr.to_json() for attr in self.attributes],
            "description": self.description,
        }

    def combine(self, node2: "Node"):
        """Overwrite attributes of self with attributes of node2."""
        if self.label != node2.label:
            raise Exception("Nodes must have the same label to be combined")

        for attr in node2.attributes:
            if attr.name not in [a.name for a in self.attributes]:
                logger.debug(f"Adding attribute {attr.name} to node {self.label}")
                self.attributes.append(attr)

        return self

    def get_unique_attributes(self):
        return [attr for attr in self.attributes if attr.unique]

    def to_graph_query(self):
        attributes = ", ".join([str(attr) for attr in self.attributes])
        if self.description:
            attributes += f"{', ' if len(attributes) > 0 else ''} {descriptionKey}: '{self.description}'"
        return f"MERGE (n:{self.label} {{{attributes}}}) RETURN n"

    def __str__(self) -> str:
        return (
            f"(:{self.label} {{{', '.join([str(attr) for attr in self.attributes])}}})"
        )
