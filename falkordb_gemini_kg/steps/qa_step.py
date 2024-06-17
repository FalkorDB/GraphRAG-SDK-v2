from falkordb_gemini_kg.steps.Step import Step
from falkordb_gemini_kg.classes.Document import Document
from falkordb_gemini_kg.classes.ontology import Ontology
from falkordb_gemini_kg.classes.model_config import KnowledgeGraphModelStepConfig
from vertexai.generative_models import GenerativeModel, ChatSession
from falkordb_gemini_kg.fixtures.prompts import GRAPH_QA_SYSTEM, GRAPH_QA_PROMPT
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QAStep(Step):
    """
    QA Step
    """

    def __init__(
        self,
        model_config: KnowledgeGraphModelStepConfig,
        config: dict = {},
    ) -> None:
        self.config = config
        self.chat_session = GenerativeModel(
            model_config.model,
            generation_config=model_config.generation_config,
            system_instruction=GRAPH_QA_SYSTEM,
        ).start_chat()

    def run(self, question: str, cypher: str, context: str):

        qa_prompt = GRAPH_QA_PROMPT.format(
            context=context, cypher=cypher, question=question
        )
        qa_response = self.chat_session.send_message(qa_prompt)

        return qa_response.text
