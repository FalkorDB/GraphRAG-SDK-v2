import re
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.node import Node
from falkordb_gemini_kg.classes.edge import Edge
import json
from falkordb_gemini_kg.helpers import (
    validate_cypher,
    validate_cypher_nodes_exist,
    validate_cypher_edges_exist,
    validate_cypher_edge_directions,
)
import unittest


import logging

logging.basicConfig(level=logging.DEBUG)


class TestValidateCypher1(unittest.TestCase):
    """
    Test a valid cypher query
    """

    cypher = """
    MATCH (f:Fighter)-[r:FOUGHT_IN]->(fight:Fight)
    RETURN f, count(fight) AS fight_count
    ORDER BY fight_count DESC
    LIMIT 1"""

    @classmethod
    def setUpClass(cls):

        cls._ontology = Ontology([], [])

        cls._ontology.add_node(
            Node(
                label="Fighter",
                attributes=[],
            )
        )

        cls._ontology.add_node(
            Node(
                label="Fight",
                attributes=[],
            )
        )

        cls._ontology.add_edge(
            Edge(
                label="FOUGHT_IN",
                source="Fighter",
                target="Fight",
                attributes=[],
            )
        )

    def test_validate_cypher_nodes_exist(self):

        errors = validate_cypher_nodes_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edges_exist(self):

        errors = validate_cypher_edges_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edge_directions(self):

        errors = validate_cypher_edge_directions(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher(self):
        errors = validate_cypher(self.cypher, self._ontology)

        assert errors is None


class TestValidateCypher2(unittest.TestCase):
    """
    Test a cypher query with the wrong edge direction
    """

    cypher = """
    MATCH (f:Fighter)<-[r:FOUGHT_IN]-(fight:Fight)
    RETURN f"""

    @classmethod
    def setUpClass(cls):

        cls._ontology = Ontology([], [])

        cls._ontology.add_node(
            Node(
                label="Fighter",
                attributes=[],
            )
        )

        cls._ontology.add_node(
            Node(
                label="Fight",
                attributes=[],
            )
        )

        cls._ontology.add_edge(
            Edge(
                label="FOUGHT_IN",
                source="Fighter",
                target="Fight",
                attributes=[],
            )
        )

    def test_validate_cypher_nodes_exist(self):

        errors = validate_cypher_nodes_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edges_exist(self):

        errors = validate_cypher_edges_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edge_directions(self):

        errors = validate_cypher_edge_directions(self.cypher, self._ontology)

        assert len(errors) == 1

    def test_validate_cypher(self):
        errors = validate_cypher(self.cypher, self._ontology)

        assert errors is not None


class TestValidateCypher3(unittest.TestCase):
    """
    Test a cypher query with multiple right edge directions
    """

    cypher = """
    MATCH (a:Airline)-[:ACCEPTS]->(p:Pet), (r:Route)-[:ALLOWS]->(sd:Service_Dog)
    RETURN a, p, r, sd
    """

    @classmethod
    def setUpClass(cls):

        cls._ontology = Ontology([], [])

        cls._ontology.add_node(
            Node(
                label="Airline",
                attributes=[],
            )
        )

        cls._ontology.add_node(
            Node(
                label="Pet",
                attributes=[],
            )
        )

        cls._ontology.add_node(
            Node(
                label="Route",
                attributes=[],
            )
        )

        cls._ontology.add_node(
            Node(
                label="Service_Dog",
                attributes=[],
            )
        )

        cls._ontology.add_edge(
            Edge(
                label="ACCEPTS",
                source="Airline",
                target="Pet",
                attributes=[],
            )
        )

        cls._ontology.add_edge(
            Edge(
                label="ALLOWS",
                source="Route",
                target="Service_Dog",
                attributes=[],
            )
        )

    def test_validate_cypher_nodes_exist(self):

        errors = validate_cypher_nodes_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edges_exist(self):

        errors = validate_cypher_edges_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_edge_directions(self):

        errors = validate_cypher_edge_directions(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher(self):
        errors = validate_cypher(self.cypher, self._ontology)

        assert errors is None or len(errors) == 0


if __name__ == "__main__":
    unittest.main()
