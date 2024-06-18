from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.source import AbstractSource
from concurrent.futures import Future, ThreadPoolExecutor, wait
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import StepModelConfig
from vertexai.generative_models import GenerativeModel, ChatSession
from falkordb_gemini_kg.fixtures.prompts import EXTRACT_DATA_SYSTEM, EXTRACT_DATA_PROMPT
import logging
from falkordb_gemini_kg.helpers import extract_json, map_dict_to_cypher_properties
import json
from falkordb import Graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ExtractDataStep(Step):
    """
    Extract Data Step
    """

    def __init__(
        self,
        sources: list[AbstractSource],
        ontology: Ontology,
        model_config: StepModelConfig,
        graph: Graph,
        config: dict = {
            "max_workers": 16,
            "max_input_tokens": 500000,
            "max_output_tokens": 8192,
        },
    ) -> None:
        self.sources = sources
        self.ontology = ontology
        self.config = config
        self.graph = graph
        self.chat_session = GenerativeModel(
            model_config.model,
            generation_config=model_config.generation_config.to_generation_config() if model_config.generation_config is not None else None,
            system_instruction=EXTRACT_DATA_SYSTEM.replace(
                "#ONTOLOGY", str(ontology.to_json())
            ),
        ).start_chat()

    def run(self):

        tasks: list[Future[Ontology]] = []
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            # extract entities and relationships from each page
            for source in self.sources:
                task = executor.submit(
                    self._process_source,
                    self.chat_session,
                    source,
                    self.ontology,
                    self.graph,
                )
                tasks.append(task)

            # Wait for all tasks to complete
            wait(tasks)

    def _process_source(
        self,
        chat_session: ChatSession,
        source: AbstractSource,
        ontology: Ontology,
        graph: Graph,
    ):
        text = next(source.load()).content[: self.config["max_input_tokens"]]
        user_message = EXTRACT_DATA_PROMPT.format(text=text)

        logger.debug(f"User message: {user_message}")
        model_response = chat_session.send_message(user_message)
        logger.debug(f"Model response: {model_response.text}")

        data = json.loads(extract_json(model_response.text))

        for node in data["nodes"]:
            try:
                self._create_node(graph, node, ontology)
            except Exception as e:
                logger.exception(e)
                continue

        for edge in data["edges"]:
            try:
                self._create_edge(graph, edge, ontology)
            except Exception as e:
                logger.exception(e)
                continue

    def _create_node(self, graph: Graph, args: dict, ontology: Ontology):
        # Get unique attributes from node
        node = ontology.get_node_with_label(args["label"])
        if node is None:
            print(f"Node with label {args['label']} not found in ontology")
            return None
        unique_attributes_schema = [attr for attr in node.attributes if attr.unique]
        unique_attributes = {
            attr.name: args["attributes"][attr.name]
            for attr in unique_attributes_schema
        }
        unique_attributes_text = map_dict_to_cypher_properties(unique_attributes)
        non_unique_attributes = {
            attr.name: args["attributes"][attr.name]
            for attr in node.attributes
            if not attr.unique and attr.name in args["attributes"]
        }
        non_unique_attributes_text = map_dict_to_cypher_properties(
            non_unique_attributes
        )
        set_statement = (
            f"SET n += {non_unique_attributes_text}"
            if len(non_unique_attributes.keys()) > 0
            else ""
        )
        query = f"MERGE (n:{args['label']} {unique_attributes_text}) {set_statement}"
        logger.debug(f"Query: {query}")
        result = graph.query(query)
        return result

    def _create_edge(self, graph: Graph, args: dict, ontology: Ontology):
        edge = ontology.get_edge_with_label(args["label"])
        if edge is None:
            print(f"Edge with label {args['label']} not found in ontology")
            return None
        source_unique_attributes = args["source"]["attributes"]
        source_unique_attributes_text = map_dict_to_cypher_properties(
            source_unique_attributes
        )

        target_unique_attributes = args["target"]["attributes"]
        target_unique_attributes_text = map_dict_to_cypher_properties(
            target_unique_attributes
        )

        edge_attributes = (
            map_dict_to_cypher_properties(args["attributes"])
            if "attributes" in args
            else {}
        )
        set_statement = (
            f"SET r += {edge_attributes}"
            if "attributes" in args and len(args["attributes"].keys()) > 0
            else ""
        )
        query = f"MATCH (s:{args['source']['label']} {source_unique_attributes_text}) MATCH (d:{args['target']['label']} {target_unique_attributes_text}) MERGE (s)-[r:{args['label']}]->(d) {set_statement}"
        logger.debug(f"Query: {query}")
        result = graph.query(query)
        return result
