import json
import logging
from .attribute import Attribute, AttributeType
from falkordb import Node as GraphNode

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, label: str, attributes: list[Attribute]):
        self.label = label
        self.attributes = attributes

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
                for attr in node.properties
            ],
        )

    @staticmethod
    def from_json(txt: dict | str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Node(
            txt["label"].replace(" ", ""),
            [Attribute.from_json(attr) for attr in txt["attributes"]],
        )

    def to_json(self):
        return {
            "label": self.label,
            "attributes": [attr.to_json() for attr in self.attributes],
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
        return f"MERGE (n:{self.label} {{{', '.join([str(attr) for attr in self.attributes])}}}) RETURN n"

    def __str__(self) -> str:
        return (
            f"(:{self.label} {{{', '.join([str(attr) for attr in self.attributes])}}})"
        )

