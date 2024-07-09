import json
from falkordb import Graph
from falkordb_gemini_kg.classes.source import AbstractSource
from falkordb_gemini_kg.models import GenerativeModel
import falkordb_gemini_kg
import logging
from .edge import Edge
from .node import Node

logger = logging.getLogger(__name__)


class Ontology(object):
    def __init__(self, nodes: list[Node] = [], edges: list[Edge] = []):
        self.nodes = nodes
        self.edges = edges

    @staticmethod
    def from_sources(
        sources: list[AbstractSource],
        boundaries: str,
        model: GenerativeModel,
    ) -> "Ontology":
        step = falkordb_gemini_kg.CreateOntologyStep(
            sources=sources,
            ontology=Ontology(),
            model=model,
        )

        return step.run(boundaries=boundaries)

    @staticmethod
    def from_json(txt: dict | str):
        txt = txt if isinstance(txt, dict) else json.loads(txt)
        return Ontology(
            [Node.from_json(node) for node in txt["nodes"]],
            [Edge.from_json(edge) for edge in txt["edges"]],
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

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

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

    def get_edges_with_label(self, label: str):
        return [e for e in self.edges if e.label == label]

    def has_node_with_label(self, label: str):
        return any(n.label == label for n in self.nodes)

    def has_edge_with_label(self, label: str):
        return any(e.label == label for e in self.edges)

    def __str__(self) -> str:
        return "Nodes:\n\f- {nodes}\n\nEdges:\n\f- {edges}".format(
            nodes="\n- ".join([str(node) for node in self.nodes]),
            edges="\n- ".join([str(edge) for edge in self.edges]),
        )

    def save_to_graph(self, graph: Graph):
        for node in self.nodes:
            query = node.to_graph_query()
            logger.debug(f"Query: {query}")
            graph.query(query)

        for edge in self.edges:
            query = edge.to_graph_query()
            logger.debug(f"Query: {query}")
            graph.query(query)
