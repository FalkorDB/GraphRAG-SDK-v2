from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import StepModelConfig
from vertexai.generative_models import GenerativeModel
from falkordb_gemini_kg.fixtures.prompts import (
    CYPHER_GEN_SYSTEM,
    CYPHER_GEN_PROMPT,
    CYPHER_GEN_PROMPT_WITH_ERROR,
)
import logging
from falkordb_gemini_kg.helpers import (
    extract_cypher,
    verify_cypher_labels,
    stringify_falkordb_response,
)
from falkordb import Graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GraphQueryGenerationStep(Step):
    """
    Graph Query Step
    """

    def __init__(
        self,
        graph: Graph,
        ontology: Ontology,
        model_config: StepModelConfig | None = None,
        config: dict = {},
        chat_session: GenerativeModel | None = None,
    ) -> None:
        assert chat_session is not None or (
            model_config is not None
        ), "Must provide either a chat session or model config"
        self.ontology = ontology
        self.config = config
        self.graph = graph
        self.chat_session = (
            chat_session
            or GenerativeModel(
                model_config.model,
            generation_config=model_config.generation_config.to_generation_config() if model_config.generation_config is not None else None,
                system_instruction=CYPHER_GEN_SYSTEM.replace(
                    "#ONTOLOGY", str(ontology.to_json())
                ),
            ).start_chat()
        )

    def run(self, question: str, retries: int = 5):
        error = False

        cypher = ""
        while error is not None and retries > 0:
            try:
                cypher_prompt = (
                    CYPHER_GEN_PROMPT.format(question=question)
                    if error is False
                    else CYPHER_GEN_PROMPT_WITH_ERROR.format(
                        question=question, error=error
                    )
                )
                cypher_statement_response = self.chat_session.send_message(
                    cypher_prompt,
                )
                cypher = extract_cypher(cypher_statement_response.text)
                logger.debug(f"Cypher: {cypher}")
                is_valid = verify_cypher_labels(cypher, self.ontology)
                # print(f"Is valid: {is_valid}")
                if is_valid is not True:
                    raise Exception(is_valid)

                if cypher is not None:
                    context = self.graph.query(cypher).result_set
                    context = stringify_falkordb_response(context)

                return (context, cypher)
            except Exception as e:
                logger.debug(f"Error: {e}")
                error = e
                retries -= 1
