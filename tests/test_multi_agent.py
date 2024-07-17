from dotenv import load_dotenv

load_dotenv()
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.entity import Entity
from falkordb_gemini_kg.classes.relation import Relation
from falkordb_gemini_kg.classes.attribute import Attribute, AttributeType
import unittest
from falkordb_gemini_kg.models.gemini import GeminiGenerativeModel
from falkordb_gemini_kg import KnowledgeGraph, KnowledgeGraphModelConfig
from falkordb_gemini_kg.classes.orchestrator import Orchestrator
from falkordb_gemini_kg.agents.kg_agent import KGAgent
import vertexai
import os
import logging
from falkordb import FalkorDB
from json import loads

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("REGION"))


class TestMultiAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.restaurants_ontology = Ontology()
        cls.restaurants_ontology.add_entity(
            Entity(
                label="Country",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                ],
            )
        )
        cls.restaurants_ontology.add_entity(
            Entity(
                label="City",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                    Attribute(
                        name="weather",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                    Attribute(
                        name="population",
                        attr_type=AttributeType.NUMBER,
                        required=False,
                        unique=False,
                    ),
                ],
            )
        )
        cls.restaurants_ontology.add_entity(
            Entity(
                label="Restaurant",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                    Attribute(
                        name="description",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                    Attribute(
                        name="rating",
                        attr_type=AttributeType.NUMBER,
                        required=False,
                        unique=False,
                    ),
                    Attribute(
                        name="food_type",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                ],
            )
        )
        cls.restaurants_ontology.add_relation(
            Relation(
                label="IN_COUNTRY",
                source="City",
                target="Country",
            )
        )
        cls.restaurants_ontology.add_relation(
            Relation(
                label="IN_CITY",
                source="Restaurant",
                target="City",
            )
        )

        cls.attractions_ontology = Ontology()
        cls.attractions_ontology.add_entity(
            Entity(
                label="Country",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                ],
            )
        )
        cls.attractions_ontology.add_entity(
            Entity(
                label="City",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                    Attribute(
                        name="weather",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                    Attribute(
                        name="population",
                        attr_type=AttributeType.NUMBER,
                        required=False,
                        unique=False,
                    ),
                ],
            )
        )
        cls.attractions_ontology.add_entity(
            Entity(
                label="Attraction",
                attributes=[
                    Attribute(
                        name="name",
                        attr_type=AttributeType.STRING,
                        required=True,
                        unique=True,
                    ),
                    Attribute(
                        name="description",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                    Attribute(
                        name="type",
                        attr_type=AttributeType.STRING,
                        required=False,
                        unique=False,
                    ),
                ],
            )
        )
        cls.attractions_ontology.add_relation(
            Relation(
                label="IN_COUNTRY",
                source="City",
                target="Country",
            )
        )
        cls.attractions_ontology.add_relation(
            Relation(
                label="IN_CITY",
                source="Attraction",
                target="City",
            )
        )

        cls.model = GeminiGenerativeModel("gemini-1.5-flash-001")
        cls.restaurants_kg = KnowledgeGraph(
            name="restaurants",
            ontology=cls.restaurants_ontology,
            model_config=KnowledgeGraphModelConfig.with_model(cls.model),
        )
        cls.attractions_kg = KnowledgeGraph(
            name="attractions",
            ontology=cls.attractions_ontology,
            model_config=KnowledgeGraphModelConfig.with_model(cls.model),
        )

        cls.import_data(cls, cls.restaurants_kg, cls.attractions_kg)

        cls.restaurants_agent = KGAgent(
            agent_id="restaurants_agent",
            kg=cls.restaurants_kg,
            introduction="""
        I'm a restaurant agent, specialized in finding the best restaurants for you. 
        """,
        )

        cls.attractions_agent = KGAgent(
            agent_id="attractions_agent",
            kg=cls.attractions_kg,
            introduction="""
        I'm an attractions agent, specialized in finding the best attractions for you. 
        """,
        )

        cls.orchestrator = Orchestrator(cls.model)

        cls.orchestrator.register_agent(cls.restaurants_agent)
        cls.orchestrator.register_agent(cls.attractions_agent)

    def import_data(
        self,
        restaurants_kg: KnowledgeGraph,
        attractions_kg: KnowledgeGraph,
    ):
        cities = loads(open("tests/data/cities.json").read())
        restaurants = loads(open("tests/data/restaurants.json").read())
        attractions = loads(open("tests/data/attractions.json").read())

        for city in cities:
            restaurants_kg.add_node(
                "City",
                {
                    "name": city["name"],
                    "weather": city["weather"],
                    "population": city["population"],
                },
            )
            restaurants_kg.add_node("Country", {"name": city["country"]})
            restaurants_kg.add_edge(
                "IN_COUNTRY",
                "City",
                "Country",
                {"name": city["name"]},
                {"name": city["country"]},
            )

            attractions_kg.add_node(
                "City",
                {
                    "name": city["name"],
                    "weather": city["weather"],
                    "population": city["population"],
                },
            )
            attractions_kg.add_node("Country", {"name": city["country"]})
            attractions_kg.add_edge(
                "IN_COUNTRY",
                "City",
                "Country",
                {"name": city["name"]},
                {"name": city["country"]},
            )

        for restaurant in restaurants:
            restaurants_kg.add_node(
                "Restaurant",
                {
                    "name": restaurant["name"],
                    "description": restaurant["description"],
                    "rating": restaurant["rating"],
                    "food_type": restaurant["food_type"],
                },
            )
            restaurants_kg.add_edge(
                "IN_CITY",
                "Restaurant",
                "City",
                {"name": restaurant["name"]},
                {"name": restaurant["city"]},
            )

        for attraction in attractions:
            attractions_kg.add_node(
                "Attraction",
                {
                    "name": attraction["name"],
                    "description": attraction["description"],
                    "type": attraction["type"],
                },
            )
            attractions_kg.add_edge(
                "IN_CITY",
                "Attraction",
                "City",
                {"name": attraction["name"]},
                {"name": attraction["city"]},
            )

    def test_multi_agent(self):

        runner = self.orchestrator.ask("Write me a 3 day itinerary for a trip to Italy")

        assert runner is not None

        assert len(runner._agents) == 2, "There should be two agents"
        assert runner._plan is not None, "Execution plan should not be None"

        response = runner.run()

        assert response is not None

        assert response.text is not None

        assert "itinerary" in response.text.lower(), f"Response should contain the 'itinerary' string: {response.text}"
