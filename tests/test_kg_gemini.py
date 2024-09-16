from dotenv import load_dotenv

load_dotenv()
from graphrag_sdk.classes.ontology import Ontology
from graphrag_sdk.classes.entity import Entity
from graphrag_sdk.classes.relation import Relation
from graphrag_sdk.classes.attribute import Attribute, AttributeType
import unittest
from graphrag_sdk.classes.source import Source
from graphrag_sdk.models.gemini import GeminiGenerativeModel
from graphrag_sdk import KnowledgeGraph, KnowledgeGraphModelConfig
import vertexai
import os
import logging
from falkordb import FalkorDB

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))


class TestKGGemini(unittest.TestCase):
    """
    Test Knowledge Graph
    """

    @classmethod
    def setUpClass(cls):

        cls.ontology = Ontology([], [])

        cls.ontology.add_entity(
            Entity(
                label="Actor",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        unique=True,
                        required=True,
                    ),
                ],
            )
        )
        cls.ontology.add_entity(
            Entity(
                label="Movie",
                attributes=[
                    Attribute(
                        name="title",
                        attr_type=AttributeType.STRING,
                        unique=True,
                        required=True,
                    ),
                ],
            )
        )
        cls.ontology.add_relation(
            Relation(
                label="ACTED_IN",
                source="Actor",
                target="Movie",
                attributes=[
                    Attribute(
                        name="role",
                        attr_type=AttributeType.STRING,
                        unique=False,
                        required=False,
                    ),
                ],
            )
        )

        cls.graph_name = "IMDB_gemini"

        model = GeminiGenerativeModel(model_name="gemini-1.5-flash-001")
        cls.kg = KnowledgeGraph(
            name=cls.graph_name,
            ontology=cls.ontology,
            model_config=KnowledgeGraphModelConfig.with_model(model),
        )

    def test_kg_creation(self):
        raise unittest.SkipTest("not ready for testing")
        file_path = "tests/data/madoff.txt"

        sources = [Source(file_path)]

        self.kg.process_sources(sources)

        (answer, chat_session) = self.kg.ask("List a few actors")

        logger.info(f"Answer: {answer}")

        assert "Joseph Scotto" in answer[0], "Joseph Scotto not found in answer"

    def test_kg_delete(self):
        raise unittest.SkipTest("not ready for testing")
        self.kg.delete()

        db = FalkorDB()
        graphs = db.list_graphs()
        self.assertNotIn(self.graph_name, graphs)
