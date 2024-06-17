import json
from falkordb import Graph, Edge as GraphEdge, Node as GraphNode

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class _AttributeType:
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"

    @staticmethod
    def fromString(txt: str):
        if txt.isdigit():
            return _AttributeType.NUMBER
        elif txt.lower() in ["true", "false"]:
            return _AttributeType.BOOLEAN
        return _AttributeType.STRING


class Attribute:
    def __init__(self, name: str, attr_type: _AttributeType, unique: bool):
        self.name = name
        self.type = attr_type
        self.unique = unique

    @staticmethod
    def from_json(txt: str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        if txt["type"] not in [
            _AttributeType.STRING,
            _AttributeType.NUMBER,
            _AttributeType.BOOLEAN,
        ]:
            raise Exception(f"Invalid attribute type: {txt['type']}")
        return Attribute(txt["name"], txt["type"], txt["unique"])

    def to_json(self):
        return {
            "name": self.name,
            "type": self.type,
            "unique": self.unique,
        }

    def __str__(self) -> str:
        return f"{self.name}: \"{self.type}{'!' if self.unique else ''}\""


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
                    _AttributeType.fromString(node.properties[attr]),
                    "!" in node.properties[attr],
                )
                for attr in node.properties
            ],
        )

    @staticmethod
    def from_json(txt: str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Node(
            txt["label"].title().replace(" ", ""),
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
        source: _EdgeNode,
        target: _EdgeNode,
        attributes: list[Attribute],
    ):
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
                )
                for attr in edge.properties
            ],
        )

    @staticmethod
    def from_json(txt: str):
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


class Ontology:
    def __init__(self, nodes: list[Node] = [], edges: list[Edge] = []):
        self.nodes = nodes
        self.edges = edges

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    @staticmethod
    def from_json(txt: str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Ontology(
            [Node.from_json(node) for node in txt["nodes"]],
            [Edge.from_json(edge) for edge in txt["edges"]],
        )

    def to_json(self):
        return {
            "nodes": [node.to_json() for node in self.nodes],
            "edges": [edge.to_json() for edge in self.edges],
        }

    def merge_with(self, o: "Ontology"):
        # Merge nodes
        for node in o.nodes:
            if node.label not in [n.label for n in self.nodes]:
                # Node does not exist in self, add it
                self.nodes.append(node)
                logger.debug(f"Adding node {node.label}")
            else:
                # Node exists in self, merge attributes
                node1 = next(n for n in self.nodes if n.label == node.label)
                node1.combine(node)

        # Merge edges
        for edge in o.edges:
            if edge.label not in [e.label for e in self.edges]:
                # Edge does not exist in self, add it
                self.edges.append(edge)
                logger.debug(f"Adding edge {edge.label}")
            else:
                # Edge exists in self, merge attributes
                edge1 = next(e for e in self.edges if e.label == edge.label)
                edge1.combine(edge)

        return self

    def discard_nodes_without_edges(self):
        nodes_to_discard = [
            node.label
            for node in self.nodes
            if all(
                [
                    edge.source.label != node.label and edge.target.label != node.label
                    for edge in self.edges
                ]
            )
        ]

        self.nodes = [node for node in self.nodes if node.label not in nodes_to_discard]
        self.edges = [
            edge
            for edge in self.edges
            if edge.source.label not in nodes_to_discard
            and edge.target.label not in nodes_to_discard
        ]

        if len(nodes_to_discard) > 0:
            logger.info(f"Discarded nodes: {', '.join(nodes_to_discard)}")

        return self

    def discard_edges_without_nodes(self):
        edges_to_discard = [
            edge.label
            for edge in self.edges
            if edge.source.label not in [node.label for node in self.nodes]
            or edge.target.label not in [node.label for node in self.nodes]
        ]

        self.edges = [edge for edge in self.edges if edge.label not in edges_to_discard]

        if len(edges_to_discard) > 0:
            logger.info(f"Discarded edges: {', '.join(edges_to_discard)}")

        return self

    def validate_nodes(self):
        # Check for nodes without unique attributes
        nodes_without_unique_attributes = [
            node.label for node in self.nodes if len(node.get_unique_attributes()) == 0
        ]
        if len(nodes_without_unique_attributes) > 0:
            logger.warn(
                f"""
*** WARNING ***
The following nodes do not have unique attributes:
{', '.join(nodes_without_unique_attributes)}
"""
            )
            return False
        return True

    def get_node_with_label(self, label: str):
        return next((n for n in self.nodes if n.label == label), None)

    def get_edge_with_label(self, label: str):
        return next((e for e in self.edges if e.label == label), None)

    def has_node_with_label(self, label: str):
        return any(n.label == label for n in self.nodes)

    def has_edge_with_label(self, label: str):
        return any(e.label == label for e in self.edges)

    def __str__(self) -> str:
        return "Nodes:\n\f- {nodes}\n\nEdges:\n\f- {edges}".format(
            nodes="\n- ".join([str(node) for node in self.nodes]),
            edges="\n- ".join([str(edge) for edge in self.edges]),
        )

    @staticmethod
    def from_graph(graph: Graph):
        ontology = Ontology()

        nodes = graph.query("MATCH (n) RETURN n").result_set
        for node in nodes:
            ontology.add_node(Node.from_graph(node[0]))

        for edge in graph.query("MATCH ()-[r]->() RETURN r").result_set:
            ontology.add_edge(Edge.from_graph(edge[0], [x for xs in nodes for x in xs]))

        return ontology

    def save_to_graph(self, graph: Graph):
        for node in self.nodes:
            query = node.to_graph_query()
            logger.debug(f"Query: {query}")
            graph.query(query)

        for edge in self.edges:
            query = edge.to_graph_query()
            logger.debug(f"Query: {query}")
            graph.query(query)
