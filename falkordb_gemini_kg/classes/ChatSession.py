from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import KnowledgeGraphModelConfig
from falkordb_gemini_kg.steps.graph_query_step import GraphQueryGenerationStep
from falkordb_gemini_kg.steps.qa_step import QAStep
from vertexai.generative_models import GenerativeModel
from falkordb_gemini_kg.fixtures.prompts import GRAPH_QA_SYSTEM, CYPHER_GEN_SYSTEM
from falkordb import Graph


class ChatSession:

    def __init__(
        self, model_config: KnowledgeGraphModelConfig, ontology: Ontology, graph: Graph
    ):
        self.model_config = model_config
        self.graph = graph
        self.ontology = ontology
        self.cypher_chat_session = GenerativeModel(
            model_config.cypher_generation.model,
            generation_config=(
                model_config.cypher_generation.generation_config.to_generation_config()
                if model_config.generation_config is not None
                else None
            ),
            system_instruction=CYPHER_GEN_SYSTEM.replace(
                "#ONTOLOGY", str(ontology.to_json())
            ),
        ).start_chat()
        self.qa_chat_session = GenerativeModel(
            model_config.qa.model,
            generation_config=(
                model_config.qa.generation_config.to_generation_config()
                if model_config.generation_config is not None
                else None
            ),
            system_instruction=GRAPH_QA_SYSTEM,
        ).start_chat()

    def send_message(self, message: str):

        cypher_step = GraphQueryGenerationStep(
            graph=self.graph,
            chat_session=self.cypher_chat_session,
            ontology=self.ontology,
        )

        (context, cypher) = cypher_step.run(message)

        qa_step = QAStep(
            chat_session=self.qa_chat_session,
        )

        answer = qa_step.run(message, cypher, context)

        return answer
