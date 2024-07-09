import re
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.entity import Entity
from falkordb_gemini_kg.classes.relation import Relation
import json
from falkordb_gemini_kg.helpers import (
    validate_cypher,
    validate_cypher_entities_exist,
    validate_cypher_relations_exist,
    validate_cypher_relation_directions,
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

        cls._ontology.add_entity(
            Entity(
                label="Fighter",
                attributes=[],
            )
        )

        cls._ontology.add_entity(
            Entity(
                label="Fight",
                attributes=[],
            )
        )

        cls._ontology.add_relation(
            Relation(
                label="FOUGHT_IN",
                source="Fighter",
                target="Fight",
                attributes=[],
            )
        )

    def test_validate_cypher_entities_exist(self):

        errors = validate_cypher_entities_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_relations_exist(self):

        errors = validate_cypher_relations_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_relation_directions(self):

        errors = validate_cypher_relation_directions(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher(self):
        errors = validate_cypher(self.cypher, self._ontology)

        assert errors is None


class TestValidateCypher2(unittest.TestCase):
    """
        Test a cypher query with the wrong relation direction
    """


    cypher = """
    MATCH (f:Fighter)<-[r:FOUGHT_IN]-(fight:Fight)
    RETURN f"""

    @classmethod
    def setUpClass(cls):

        cls._ontology = Ontology([], [])

        cls._ontology.add_entity(
            Entity(
                label="Fighter",
                attributes=[],
            )
        )

        cls._ontology.add_entity(
            Entity(
                label="Fight",
                attributes=[],
            )
        )

        cls._ontology.add_relation(
            Relation(
                label="FOUGHT_IN",
                source="Fighter",
                target="Fight",
                attributes=[],
            )
        )

    def test_validate_cypher_entities_exist(self):

        errors = validate_cypher_entities_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_relations_exist(self):

        errors = validate_cypher_relations_exist(self.cypher, self._ontology)

        assert len(errors) == 0

    def test_validate_cypher_relation_directions(self):

        errors = validate_cypher_relation_directions(self.cypher, self._ontology)

        assert len(errors) == 1

    def test_validate_cypher(self):
        errors = validate_cypher(self.cypher, self._ontology)

        assert errors is not None


if __name__ == "__main__":
    unittest.main()
