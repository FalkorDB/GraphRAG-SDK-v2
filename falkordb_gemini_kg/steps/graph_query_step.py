from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.models import (
    GenerativeModelChatSession,
)
from falkordb_gemini_kg.fixtures.prompts import (
    CYPHER_GEN_SYSTEM,
    CYPHER_GEN_PROMPT,
    CYPHER_GEN_PROMPT_WITH_ERROR,
)
import logging
from falkordb_gemini_kg.helpers import (
    extract_cypher,
    validate_cypher,
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
        chat_session: GenerativeModelChatSession,
        config: dict = {},
    ) -> None:
        self.ontology = ontology
        self.config = config
        self.graph = graph
        self.chat_session = chat_session

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
                logger.debug(f"Cypher Prompt: {cypher_prompt}")
                cypher_statement_response = self.chat_session.send_message(
                    cypher_prompt,
                )
                cypher = extract_cypher(cypher_statement_response.text)
                logger.debug(f"Cypher: {cypher}")
                validation_errors = validate_cypher(cypher, self.ontology)
                # print(f"Is valid: {is_valid}")
                if validation_errors is not None:
                    raise Exception("\n".join(validation_errors))

                if cypher is not None:
                    result_set = self.graph.query(cypher).result_set
                    context = stringify_falkordb_response(result_set)
                    logger.debug(f"Context: {context}")
                    logger.debug(f"Context size: {len(result_set)}")
                    logger.debug(f"Context characters: {len(str(context))}")

                return (context, cypher)
            except Exception as e:
                logger.debug(f"Error: {e}")
                error = e
                retries -= 1

        raise Exception("Failed to generate Cypher query: " + str(error))
