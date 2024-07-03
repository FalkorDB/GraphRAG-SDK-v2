import json
import re
import logging
from .attribute import Attribute, _AttributeType
from falkordb import Node as GraphNode, Edge as GraphEdge
from falkordb_gemini_kg.fixtures.regex import *

logger = logging.getLogger(__name__)

class _EdgeNode:
    def __init__(self, label: str):
        self.label = label

    @staticmethod
    def from_json(txt: str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return _EdgeNode(txt["label"])

    def to_json(self):
        return {"label": self.label}

    def __str__(self) -> str:
        return f"(:{self.label})"


class Edge:
    def __init__(
        self,
        label: str,
        source: _EdgeNode | str,
        target: _EdgeNode | str, 
        attributes: list[Attribute],
    ):
        
        if isinstance(source, str):
            source = _EdgeNode(source)
        if isinstance(target, str):
            target = _EdgeNode(target)
        
        assert isinstance(label, str), "Label must be a string"
        assert isinstance(source, _EdgeNode), "Source must be an EdgeNode"
        assert isinstance(target, _EdgeNode), "Target must be an EdgeNode"
        assert isinstance(attributes, list), "Attributes must be a list"


        self.label = label
        self.source = source
        self.target = target
        self.attributes = attributes

    @staticmethod
    def from_graph(edge: GraphEdge, nodes: list[GraphNode]):
        logger.debug(f"Edge.from_graph: {edge}")
        return Edge(
            edge.relation,
            _EdgeNode(next(n.labels[0] for n in nodes if n.id == edge.src_node)),
            _EdgeNode(next(n.labels[0] for n in nodes if n.id == edge.dest_node)),
            [
                Attribute(
                    attr,
                    _AttributeType.fromString(edge.properties),
                    "!" in edge.properties[attr],
                    "*" in edge.properties[attr],
                )
                for attr in edge.properties
            ],
        )

    @staticmethod
    def from_json(txt: dict | str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Edge(
            txt["label"],
            _EdgeNode.from_json(txt["source"]),
            _EdgeNode.from_json(txt["target"]),
            (
                [Attribute.from_json(attr) for attr in txt["attributes"]]
                if "attributes" in txt
                else []
            ),
        )

    @staticmethod
    def from_string(txt: str):
        label = re.search(EDGE_LABEL_REGEX, txt).group(0).strip()
        source = re.search(NODE_LABEL_REGEX, txt).group(0).strip()
        target = re.search(NODE_LABEL_REGEX, txt).group(1).strip()
        edge = re.search(EDGE_REGEX, txt).group(0)
        attributes = (
            edge.split("{")[1].split("}")[0].strip().split(",") if "{" in edge else []
        )

        return Edge(
            label,
            _EdgeNode(source),
            _EdgeNode(target),
            [Attribute.from_string(attr) for attr in attributes],
        )

    def to_json(self):
        return {
            "label": self.label,
            "source": self.source.to_json(),
            "target": self.target.to_json(),
            "attributes": [attr.to_json() for attr in self.attributes],
        }

    def combine(self, edge2: "Edge"):
        """Overwrite attributes of self with attributes of edge2."""
        if self.label != edge2.label:
            raise Exception("Edges must have the same label to be combined")

        for attr in edge2.attributes:
            if attr.name not in [a.name for a in self.attributes]:
                logger.debug(f"Adding attribute {attr.name} to edge {self.label}")
                self.attributes.append(attr)

        return self

    def to_graph_query(self):
        return f"MATCH (s:{self.source.label}) MATCH (t:{self.target.label}) MERGE (s)-[r:{self.label} {{{', '.join([str(attr) for attr in self.attributes])}}}]->(t) RETURN r"

    def __str__(self) -> str:
        return f"{self.source}-[:{self.label} {{{', '.join([str(attr) for attr in self.attributes])}}}]->{self.target}"
